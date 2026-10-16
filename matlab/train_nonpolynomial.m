function train_nonpolynomial(iterations)
% New derivative-only training example, NOT the missing historical script.
% Do not expect these weights to match the supplementary checkpoint.
if nargin<1, iterations=5000; end
assert(iterations>=1 && iterations==floor(iterations));
rng(20261016,'twister');
layers=[featureInputLayer(2,'Normalization','none','Name','x'); ...
    fullyConnectedLayer(8,'Name','feature1','BiasLearnRateFactor',0); ...
    tanhLayer('Name','tanh1'); ...
    fullyConnectedLayer(4,'Name','feature2','BiasLearnRateFactor',0); ...
    tanhLayer('Name','tanh2')];
net=dlnetwork(layers);
% Biases are initialized to zero and remain fixed, giving a bias-free map.
avg=[]; avgSq=[];
for k=1:iterations
    X=dlarray(single(3.8*rand(2,2048)-1.9),'CB');
    [loss,grad]=dlfeval(@objective,net,X);
    [net,avg,avgSq]=adamupdate(net,grad,avg,avgSq,k,1e-3);
    if k==1 || mod(k,500)==0
        fprintf('%d/%d loss=%g\n',k,iterations,double(extractdata(loss)));
    end
end
repo=fileparts(fileparts(mfilename('fullpath')));
outDir=fullfile(repo,'generated','nonpolynomial_training');
if ~exist(outDir,'dir'), mkdir(outDir); end
metadata=struct('Seed',20261016,'Iterations',iterations,'BatchSize',2048, ...
    'LearningRate',1e-3,'Epsilon',0.02,'Decay',0.03,'Offset',0.05, ...
    'Provenance','Reconstructed training example, not the historical script');
save(fullfile(outDir,'retrained_network.mat'),'net','metadata');
end

function [loss,grad]=objective(net,X)
x=stripdims(X); feat=stripdims(forward(net,X));
feat0=stripdims(forward(net,dlarray(zeros(2,1,'single'),'CB')));
q=sum(x.^2,1); V=0.02*q+sum((feat-feat0).^2,1);
g=stripdims(dlgradient(sum(V,'all'),X,'EnableHigherDerivatives',true));
F=[-x(1,:)+x(1,:).*x(2,:);-x(2,:)]; dotV=sum(g.*F,1);
margin=dotV+0.03*q;
loss=mean(((dotV+q)./(q+0.05)).^2,'all')+ ...
    8*mean((max(margin,0)./(q+0.05)).^2,'all');
grad=dlgradient(loss,net.Learnables);
end
