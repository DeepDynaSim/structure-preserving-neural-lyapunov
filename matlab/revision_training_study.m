function revision_training_study(baseFile,outDir)
% Public repository copy. Historical algorithm; see docs/VERIFICATION_STATUS.md.
% Fixed padding does not establish validated outward rounding.
% Peer-review revision experiments for neural Lyapunov candidate learning.
% MATLAB R2024b. All training runs use CPU execution and single precision.

rootDir = fileparts(mfilename("fullpath"));
if nargin<1, baseFile=fullfile(rootDir,"..","results","base","neural_lyapunov_results.mat"); end
if nargin<2, outDir=fullfile(rootDir,"..","generated","revision"); end
if ~exist(outDir,"dir"), mkdir(outDir); end
set(groot,"defaultAxesFontName","Arial");
set(groot,"defaultTextFontName","Arial");
set(groot,"defaultAxesFontSize",10);
set(groot,"defaultLineLineWidth",1.5);

base = load(baseFile);
sys = main_system(base.A,base.P,base.J);
cfg = default_config(2);
cfg.seed = 20260826;
cfg.iterations = 2200;
cfg.anchorWeight = 0;             % principal revision uses no privileged V* anchors
cfg.useHard = true;
cfg.useNear = true;
cfg.useNormalization = true;
cfg.useHinge = true;
cfg.hingeWeight = 8;
cfg.epsilon = 0.02;
cfg.decay = 0.15;
cfg.offset = 0.05;
cfg.domainRadius = 2;
cfg.hidden = [24 8];

fprintf("[1/6] Building independent validation and untouched final test sets...\n");
rng(314159,"twister");
Xvalidation = single((2*rand(2,50000)-1)*cfg.domainRadius);

fprintf("[2/6] Ten independent no-anchor principal runs...\n");
seeds = (20260826:20260835)';
nSeeds = numel(seeds);
nets = cell(nSeeds,1);
valStats = repmat(empty_stats(),nSeeds,1);
trainTimes = zeros(nSeeds,1);
counterexampleUpdates = zeros(nSeeds,1);
for k=1:nSeeds
    cfg.seed=seeds(k);
    rng(cfg.seed,"twister");
    [nets{k},hist,trainTimes(k),counterexampleUpdates(k)] = train_positive(sys,cfg);
    valStats(k)=evaluate_positive(nets{k},sys,cfg,Xvalidation,[]);
    fprintf("  seed %d: val max ratio %.4e, PDE RMSE %.4e, time %.2f s\n", ...
        seeds(k),valStats(k).max_margin_ratio,valStats(k).pde_rmse,trainTimes(k));
end

validScores = [valStats.max_margin_ratio]';
successCandidates = find(validScores<=1e-8);
if isempty(successCandidates)
    [~,chosenIndex]=min(validScores);
else
    [~,j]=min([valStats(successCandidates).pde_rmse]);
    chosenIndex=successCandidates(j);
end
chosenNet=nets{chosenIndex}; chosenSeed=seeds(chosenIndex);

% The final test set is instantiated only after model selection.
rng(271828,"twister");
axisGrid=linspace(-cfg.domainRadius,cfg.domainRadius,181);
[G1,G2]=meshgrid(axisGrid,axisGrid);
Xgrid=single([G1(:)';G2(:)']);
XtestRandom=single((2*rand(2,200000)-1)*cfg.domainRadius);
Xtest=[Xgrid,XtestRandom];

testStats=repmat(empty_stats(),nSeeds,1);
for k=1:nSeeds
    testStats(k)=evaluate_positive(nets{k},sys,cfg,Xtest,[]);
end
success = [testStats.margin_violation_rate]'==0 & [testStats.positive_violation_rate]'==0;
multiSeedTable = table(seeds,trainTimes,[testStats.pde_rmse]',[testStats.max_margin_all]', ...
    [testStats.max_margin_off_origin]',[testStats.max_margin_ratio]', ...
    [testStats.margin_violation_rate]',[testStats.derivative_violation_rate]', ...
    counterexampleUpdates,success, ...
    'VariableNames',{'Seed','TrainingTime_s','PDERMSE','MaxMarginAll','MaxMarginOffOrigin', ...
    'MaxMarginRatio','MarginViolationRate','DerivativeViolationRate','HardPoolUpdates','SampledGateSuccess'});
    writetable(multiSeedTable,fullfile(outDir,"multiseed_metrics.csv"));

summaryTable=table(mean(trainTimes),std(trainTimes),mean([testStats.pde_rmse]),std([testStats.pde_rmse]), ...
    mean([testStats.max_margin_ratio]),std([testStats.max_margin_ratio]),mean(success), ...
    min([testStats.max_margin_off_origin]),max([testStats.max_margin_off_origin]),chosenSeed, ...
    'VariableNames',{'MeanTrainingTime_s','StdTrainingTime_s','MeanPDERMSE','StdPDERMSE', ...
    'MeanMaxMarginRatio','StdMaxMarginRatio','SampledSuccessRate','BestMaxMarginOffOrigin', ...
    'WorstMaxMarginOffOrigin','ValidationSelectedSeed'});
writetable(summaryTable,fullfile(outDir,"multiseed_summary.csv"));

alpha=0.05; mcN=size(XtestRandom,2);
% Count the selected model's declared event on the IID sample alone.
[~,~,mcNorm2,mcMargin]=dlfeval(@positive_quantities,chosenNet, ...
    dlarray(XtestRandom,"CB"),sys,cfg,false);
mcNorm2=double(gather(extractdata(mcNorm2)));
mcMargin=double(gather(extractdata(mcMargin)));
observedFailures=sum(mcNorm2>1e-8 & mcMargin>1e-10);
if observedFailures==0
    binomialUpper=-expm1(log(alpha)/mcN);
else
    binomialUpper=NaN; % zero-event formula is inapplicable
end
confidenceTable=table(mcN,observedFailures,0.95,binomialUpper, ...
    'VariableNames',{'IIDMonteCarloTrials','ObservedFailures','OneSidedConfidenceLevel','ClopperPearsonUpper'});
writetable(confidenceTable,fullfile(outDir,"monte_carlo_confidence.csv"));

fprintf("[3/6] Controlled cumulative ablation study...\n");
ablationNames=["Positive value regression","+ transport residual","+ decay hinge", ...
    "+ near-origin sampling","+ normalization","+ privileged anchors", ...
    "+ hard-state recycling","Full without anchors"]';
ablationCfg=cell(numel(ablationNames),1);
for k=1:numel(ablationNames)
    a=cfg; a.seed=20260826; a.iterations=1600; a.useHard=false; a.useNear=false;
    a.useNormalization=false; a.useHinge=false; a.anchorWeight=0; a.objective="pde";
    if k==1, a.objective="value"; end
    if k>=3, a.useHinge=true; end
    if k>=4, a.useNear=true; end
    if k>=5, a.useNormalization=true; end
    if k==6 || k==7, a.anchorWeight=0.05; end
    if k>=7, a.useHard=true; end
    if k==8, a.anchorWeight=0; end
    ablationCfg{k}=a;
end
ablationRows=cell(numel(ablationNames),1);
for k=1:numel(ablationNames)
    a=ablationCfg{k}; rng(a.seed,"twister");
    [net,~,elapsed,updates]=train_positive(sys,a);
    st=evaluate_positive(net,sys,a,Xtest,base.P);
    ablationRows{k}={ablationNames(k),elapsed,st.value_rel_l2,st.pde_rmse, ...
        st.max_margin_ratio,st.positive_violation_rate,st.derivative_violation_rate, ...
        st.margin_violation_rate,updates,a.anchorWeight};
    fprintf("  %s: max ratio %.3e, violation %.3e\n",ablationNames(k),st.max_margin_ratio,st.margin_violation_rate);
end
ablationTable=cell2table(vertcat(ablationRows{:}),'VariableNames', ...
    {'Variant','TrainingTime_s','RelativeL2ValueError','PDERMSE','MaxMarginRatio', ...
    'PositiveViolationRate','DerivativeViolationRate','MarginViolationRate','HardPoolUpdates','AnchorWeight'});
writetable(ablationTable,fullfile(outDir,"ablation_metrics.csv"));

fprintf("[4/6] Derivative-trained unconstrained comparator...\n");
ucfg=cfg; ucfg.seed=20260826; ucfg.iterations=2200;
rng(ucfg.seed,"twister");
[unconstrainedNet,unconstrainedTime]=train_unconstrained(sys,ucfg);
unconstrainedStats=evaluate_unconstrained(unconstrainedNet,sys,ucfg,Xtest,base.P);
unconstrainedTable=struct2table(unconstrainedStats);
unconstrainedTable.TrainingTime_s=unconstrainedTime;
writetable(unconstrainedTable,fullfile(outDir,"derivative_unconstrained_metrics.csv"));

fprintf("[5/6] One-factor-at-a-time sensitivity screening...\n");
[sensitivityTable,sensitivityNets]=run_sensitivity(sys,cfg,Xvalidation);
writetable(sensitivityTable,fullfile(outDir,"sensitivity_metrics.csv"));

fprintf("[6/6] Robotic and higher-dimensional benchmark expansion...\n");
[benchmarkTable,benchmarkData]=run_benchmarks(chosenNet,sys,cfg);
writetable(benchmarkTable,fullfile(outDir,"benchmark_suite_metrics.csv"));

make_multiseed_figure(multiSeedTable,outDir);
make_ablation_sensitivity_figure(ablationTable,sensitivityTable,outDir);
make_benchmark_figure(benchmarkTable,benchmarkData,outDir);

hardware=struct;
hardware.MATLABVersion=version;
hardware.CPU="11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz";
hardware.PhysicalCores=feature('numcores');
hardware.LogicalProcessors=16;
hardware.Execution="CPU, single-precision network training; vectorized mini-batches";
hardware.ValidationSeed=314159;
hardware.FinalTestSeed=271828;
hardware.ODEIntegrator="ode45; RelTol=1e-9; AbsTol=1e-11";

save(fullfile(outDir,"revision_experiments.mat"),"chosenNet","chosenSeed","nets", ...
    "multiSeedTable","summaryTable","confidenceTable","ablationTable", ...
    "sensitivityTable","sensitivityNets","benchmarkTable","benchmarkData", ...
    "unconstrainedNet","unconstrainedStats","sys","cfg","hardware");

fid=fopen(fullfile(outDir,"revision_run_log.txt"),'w');
fprintf(fid,"MATLAB %s\n",version);
fprintf(fid,"CPU: %s; physical cores used by MATLAB: %d; logical processors: 16\n",hardware.CPU,hardware.PhysicalCores);
fprintf(fid,"Principal method: no analytical anchors; validation seed 314159; untouched final test seed 271828\n");
fprintf(fid,"Selected seed: %d; multi-seed sampled success rate: %.6f\n",chosenSeed,mean(success));
fprintf(fid,"Zero-failure one-sided 95%% binomial upper bound for N=%d: %.9g\n",mcN,binomialUpper);
fprintf(fid,"Tolerances: origin excluded when ||x||^2<=1e-8; inequality violation if value exceeds +1e-10; positivity violation if V<-1e-10.\n");
fclose(fid);
fprintf("Revision outputs written to %s\n",outDir);
end

function sys=main_system(A,P,J)
sys.type="main"; sys.n=2; sys.A=single(A); sys.P=single(P); sys.J=single(J); sys.name="Auditable nonlinear benchmark";
end

function cfg=default_config(n)
cfg=struct('seed',1,'iterations',1000,'uniformBatch',704,'nearBatch',128,'hardBatch',192, ...
    'hardPool',12000,'recycleInterval',200,'useHard',true,'useNear',true, ...
    'useNormalization',true,'useHinge',true,'hingeWeight',8,'anchorWeight',0, ...
    'epsilon',0.02,'decay',0.15,'offset',0.05,'domainRadius',2, ...
    'hidden',[24 8],'objective',"pde",'n',n);
end

function [net,history,elapsed,updates]=train_positive(sys,cfg)
net=make_feature_net(cfg.n,cfg.hidden);
net=scale_network(net,0.25);
hardPoints=single((2*rand(cfg.n,cfg.hardBatch)-1)*cfg.domainRadius);
history.loss=zeros(cfg.iterations,1); history.pde=zeros(cfg.iterations,1); history.margin=zeros(cfg.iterations,1);
avgGrad=[]; avgSqGrad=[]; updates=0; tic;
for iter=1:cfg.iterations
    Xu=single((2*rand(cfg.n,cfg.uniformBatch)-1)*cfg.domainRadius);
    X=Xu;
    if cfg.useNear
        Xn=single(0.25*randn(cfg.n,cfg.nearBatch));
        Xn=max(min(Xn,cfg.domainRadius),-cfg.domainRadius);
        X=[X,Xn];
    end
    if cfg.useHard
        X=[X,hardPoints(:,randi(size(hardPoints,2),1,cfg.hardBatch))];
    end
    [loss,grad,pde,maxMargin]=dlfeval(@positive_loss,net,dlarray(X,"CB"),sys,cfg);
    lr=1.5e-3*(0.2+0.8*0.5*(1+cos(pi*(iter-1)/cfg.iterations)));
    [net,avgGrad,avgSqGrad]=adamupdate(net,grad,avgGrad,avgSqGrad,iter,lr);
    history.loss(iter)=double(gather(extractdata(loss)));
    history.pde(iter)=double(gather(extractdata(pde)));
    history.margin(iter)=double(gather(extractdata(maxMargin)));
    if cfg.useHard && mod(iter,cfg.recycleInterval)==0
        pool=single((2*rand(cfg.n,cfg.hardPool)-1)*cfg.domainRadius);
        [~,~,~,m]=dlfeval(@positive_quantities,net,dlarray(pool,"CB"),sys,cfg,false);
        m=gather(extractdata(m)); [~,idx]=maxk(m,cfg.hardBatch); hardPoints=pool(:,idx); updates=updates+1;
    end
end
elapsed=toc;
end

function [loss,grad,pdeRMSE,maxMargin]=positive_loss(net,X,sys,cfg)
[V,dotV,norm2,margin]=positive_quantities(net,X,sys,cfg,true);
denom=ones(size(norm2),'like',norm2);
if cfg.useNormalization, denom=norm2+cfg.offset; end
residual=(dotV+norm2)./denom;
if cfg.objective=="value"
    Xu=stripdims(X); Vstar=sum(Xu.*(sys.P*Xu),1);
    loss=mean(((V-Vstar)./(Vstar+0.1)).^2,'all');
else
    loss=mean(residual.^2,'all');
    if cfg.useHinge
        loss=loss+cfg.hingeWeight*mean((max(margin,0)./denom).^2,'all');
    end
    if cfg.anchorWeight>0 && sys.type=="main"
        anchors=single([1.5,-1.5,1.0,-1.0;1.0,-1.0,-1.5,1.5]);
        Va=positive_values(net,dlarray(anchors,"CB"),cfg.epsilon);
        Vstar=sum(anchors.*(sys.P*anchors),1);
        loss=loss+cfg.anchorWeight*mean(((Va-Vstar)./(Vstar+0.1)).^2,'all');
    end
end
grad=dlgradient(loss,net.Learnables);
pdeRMSE=sqrt(mean((dotV+norm2).^2,'all')); maxMargin=max(margin,[],'all');
end

function V=positive_values(net,X,epsilon)
Xu=stripdims(X); feat=stripdims(forward(net,X));
z=dlarray(zeros(size(Xu,1),1,'single'),"CB"); feat0=stripdims(forward(net,z));
V=epsilon*sum(Xu.^2,1)+sum((feat-feat0).^2,1);
end

function [V,dotV,norm2,margin,gradV]=positive_quantities(net,X,sys,cfg,higher)
V=positive_values(net,X,cfg.epsilon);
gradV=stripdims(dlgradient(sum(V,'all'),X,'EnableHigherDerivatives',higher));
F=system_field(X,sys); norm2=sum(stripdims(X).^2,1);
dotV=sum(gradV.*F,1); margin=dotV+cfg.decay*norm2;
end

function F=system_field(X,sys)
Xu=stripdims(X);
switch sys.type
    case "main"
        PX=sys.P*Xu; F=sys.A*Xu+(sys.J*PX).*(0.6*Xu(1,:));
    case "pendulum"
        theta=Xu(1,:); omega=Xu(2,:);
        u=sys.umax*tanh((-sys.k1*theta-sys.k2*omega)/sys.umax);
        F=[omega;sin(theta)+u];
    case "oscillator4"
        x1=Xu(1,:); x2=Xu(2,:); x3=Xu(3,:); x4=Xu(4,:);
        F=[x2;-2*x1-1.2*x2-0.2*x1.^3+0.15*x3; ...
           x4;-1.5*x3-1.0*x4-0.15*x3.^3+0.15*x1];
end
end

function net=make_feature_net(n,hidden)
layers=featureInputLayer(n,"Normalization","none","Name","state");
for k=1:numel(hidden)
    layers=[layers;fullyConnectedLayer(hidden(k),"Name","feature"+k)]; %#ok<AGROW>
    if k<numel(hidden), layers=[layers;tanhLayer("Name","tanh"+k)]; end %#ok<AGROW>
end
net=dlnetwork(layers);
end

function net=scale_network(net,scale)
for i=1:size(net.Learnables,1)
    value=net.Learnables.Value{i};
    if contains(net.Learnables.Parameter(i),"Weights"), net.Learnables.Value{i}=value*scale;
    else, net.Learnables.Value{i}=value*0; end
end
end

function st=evaluate_positive(net,sys,cfg,X,Pexact)
[V,dV,n2,m]=dlfeval(@positive_quantities,net,dlarray(X,"CB"),sys,cfg,false);
V=double(gather(extractdata(V))); dV=double(gather(extractdata(dV)));
n2=double(gather(extractdata(n2))); m=double(gather(extractdata(m)));
mask=n2>1e-8; st=empty_stats();
st.origin_value=min(abs(V(n2<=1e-12)));
st.min_value_off_origin=min(V(mask));
st.positive_violation_rate=mean(V(mask)<-1e-10);
st.derivative_violation_rate=mean(dV(mask)>1e-10);
st.margin_violation_rate=mean(m(mask)>1e-10);
st.max_margin_all=max(m); st.max_margin_off_origin=max(m(mask));
st.max_margin_ratio=max(m(mask)./n2(mask)); st.pde_rmse=sqrt(mean((dV+n2).^2));
st.minimum_normalized_decay=min(-dV(mask)./n2(mask));
if ~isempty(Pexact)
    Xd=double(X); Vstar=sum(Xd.*(double(Pexact)*Xd),1);
    st.value_rel_l2=norm(V-Vstar)/norm(Vstar);
else
    st.value_rel_l2=NaN;
end
end

function st=empty_stats
st=struct('origin_value',NaN,'min_value_off_origin',NaN,'positive_violation_rate',NaN, ...
    'derivative_violation_rate',NaN,'margin_violation_rate',NaN,'max_margin_all',NaN, ...
    'max_margin_off_origin',NaN,'max_margin_ratio',NaN,'pde_rmse',NaN, ...
    'minimum_normalized_decay',NaN,'value_rel_l2',NaN);
end

function [net,elapsed]=train_unconstrained(sys,cfg)
layers=[featureInputLayer(cfg.n,"Normalization","none","Name","state"); ...
    fullyConnectedLayer(32,"Name","fc1");tanhLayer("Name","t1"); ...
    fullyConnectedLayer(32,"Name","fc2");tanhLayer("Name","t2"); ...
    fullyConnectedLayer(1,"Name","out")];
net=dlnetwork(layers); net=scale_network(net,0.25); avg=[]; avgsq=[]; tic;
for iter=1:cfg.iterations
    X=single((2*rand(cfg.n,1024)-1)*cfg.domainRadius);
    [loss,grad]=dlfeval(@unconstrained_loss,net,dlarray(X,"CB"),sys,cfg);
    lr=1.5e-3*(0.2+0.8*0.5*(1+cos(pi*(iter-1)/cfg.iterations)));
    [net,avg,avgsq]=adamupdate(net,grad,avg,avgsq,iter,lr);
end
elapsed=toc;
end

function [loss,grad]=unconstrained_loss(net,X,sys,cfg)
[V,dV,n2,m]=unconstrained_quantities(net,X,sys,cfg,true);
den=n2+cfg.offset;
loss=mean(((dV+n2)./den).^2,'all')+8*mean((max(m,0)./den).^2,'all')+ ...
    8*mean((max(cfg.epsilon*n2-V,0)./den).^2,'all');
grad=dlgradient(loss,net.Learnables);
end

function [V,dV,n2,m]=unconstrained_quantities(net,X,sys,cfg,higher)
raw=stripdims(forward(net,X)); z=dlarray(zeros(cfg.n,1,'single'),"CB");
V=raw-stripdims(forward(net,z));
g=stripdims(dlgradient(sum(V,'all'),X,'EnableHigherDerivatives',higher));
F=system_field(X,sys); n2=sum(stripdims(X).^2,1); dV=sum(g.*F,1); m=dV+cfg.decay*n2;
end

function st=evaluate_unconstrained(net,sys,cfg,X,Pexact)
[V,dV,n2,m]=dlfeval(@unconstrained_quantities,net,dlarray(X,"CB"),sys,cfg,false);
V=double(gather(extractdata(V)));dV=double(gather(extractdata(dV)));n2=double(gather(extractdata(n2)));m=double(gather(extractdata(m)));
mask=n2>1e-8; Xd=double(X); Vstar=sum(Xd.*(double(Pexact)*Xd),1);
st=struct('OriginValue',min(abs(V(n2<=1e-12))),'MinimumValueOffOrigin',min(V(mask)), ...
    'PositiveViolationRate',mean(V(mask)<-1e-10),'DerivativeViolationRate',mean(dV(mask)>1e-10), ...
    'MarginViolationRate',mean(m(mask)>1e-10),'MaximumMarginRatio',max(m(mask)./n2(mask)), ...
    'PDERMSE',sqrt(mean((dV+n2).^2)),'RelativeL2ValueError',norm(V-Vstar)/norm(Vstar));
end

function [T,nets]=run_sensitivity(sys,cfg,Xvalidation)
names=["reference","epsilon=0.01","epsilon=0.04","c=0.10","c=0.20", ...
    "hinge=4","hinge=12","offset=0.02","offset=0.10","anchors=0.05", ...
    "hard=96","hard=384","recycle=100","recycle=400","width=16", ...
    "width=32","depth=2"]';
n=numel(names); nets=cell(n,1); values=zeros(n,7);
for k=1:n
    s=cfg; s.seed=404000+k; s.iterations=1000; s.anchorWeight=0;
    switch k
        case 2, s.epsilon=0.01;
        case 3, s.epsilon=0.04;
        case 4, s.decay=0.10;
        case 5, s.decay=0.20;
        case 6, s.hingeWeight=4;
        case 7, s.hingeWeight=12;
        case 8, s.offset=0.02;
        case 9, s.offset=0.10;
        case 10, s.anchorWeight=0.05;
        case 11, s.hardBatch=96;
        case 12, s.hardBatch=384;
        case 13, s.recycleInterval=100;
        case 14, s.recycleInterval=400;
        case 15, s.hidden=[16 8];
        case 16, s.hidden=[32 12];
        case 17, s.hidden=[24 24 8];
    end
    rng(s.seed,"twister"); [nets{k},~,elapsed,updates]=train_positive(sys,s);
    st=evaluate_positive(nets{k},sys,s,Xvalidation,[]);
    values(k,:)=[elapsed,st.pde_rmse,st.max_margin_ratio,st.margin_violation_rate, ...
        st.derivative_violation_rate,updates,st.min_value_off_origin];
    fprintf("  sensitivity %s: ratio %.3e, PDE %.3e\n",names(k),st.max_margin_ratio,st.pde_rmse);
end
T=table(names,values(:,1),values(:,2),values(:,3),values(:,4),values(:,5),values(:,6),values(:,7), ...
    'VariableNames',{'Configuration','TrainingTime_s','PDERMSE','MaxMarginRatio','MarginViolationRate', ...
    'DerivativeViolationRate','HardPoolUpdates','MinimumValueOffOrigin'});
end

function [T,data]=run_benchmarks(mainNet,mainSys,mainCfg)
systems=cell(3,1); cfgs=cell(3,1); nets=cell(3,1);
systems{1}=mainSys; cfgs{1}=mainCfg; nets{1}=mainNet;
pend=struct('type',"pendulum",'n',2,'umax',single(3),'k1',single(4),'k2',single(2.5),'name',"Torque-saturated inverted pendulum");
pcfg=default_config(2); pcfg.seed=505001; pcfg.iterations=2200; pcfg.domainRadius=1.25; pcfg.decay=0.05; pcfg.hidden=[24 8]; pcfg.anchorWeight=0;
systems{2}=pend; cfgs{2}=pcfg; rng(pcfg.seed,"twister"); [nets{2},~,~,~]=train_positive(pend,pcfg);
osc=struct('type',"oscillator4",'n',4,'name',"Four-state coupled nonlinear oscillators");
ocfg=default_config(4); ocfg.seed=505002; ocfg.iterations=2400; ocfg.domainRadius=1.25; ocfg.decay=0.05; ocfg.hidden=[32 12]; ocfg.uniformBatch=768; ocfg.anchorWeight=0;
systems{3}=osc; cfgs{3}=ocfg; rng(ocfg.seed,"twister"); [nets{3},~,~,~]=train_positive(osc,ocfg);
names=strings(3,1); dims=zeros(3,1); decay=zeros(3,1); pde=zeros(3,1); maxRatio=zeros(3,1); viol=zeros(3,1); trajViol=zeros(3,1); finalNorm=zeros(3,1);
data=cell(3,1);
for k=1:3
    rng(606000+k,"twister"); X=single((2*rand(systems{k}.n,120000)-1)*cfgs{k}.domainRadius);
    st=evaluate_positive(nets{k},systems{k},cfgs{k},X,[]);
    [trajViol(k),finalNorm(k),data{k}]=trajectory_benchmark(nets{k},systems{k},cfgs{k});
    names(k)=systems{k}.name; dims(k)=systems{k}.n; decay(k)=cfgs{k}.decay; pde(k)=st.pde_rmse; maxRatio(k)=st.max_margin_ratio; viol(k)=st.margin_violation_rate;
end
T=table(names,dims,decay,pde,maxRatio,viol,trajViol,finalNorm, ...
    'VariableNames',{'Benchmark','Dimension','DecayRate','PDERMSE','MaxMarginRatio','MarginViolationRate','TrajectoryViolationRate','MaximumFinalNorm'});
end

function [violRate,maxFinal,data]=trajectory_benchmark(net,sys,cfg)
rng(707000+sys.n,"twister"); nTraj=12; initials=randn(sys.n,nTraj); initials=initials./vecnorm(initials).*min(0.7*cfg.domainRadius,1.0);
viol=0; steps=0; final=zeros(nTraj,1); data=cell(nTraj,1);
for k=1:nTraj
    [t,x]=ode45(@(~,x)numeric_field(x,sys),[0 12],double(initials(:,k)),odeset('RelTol',1e-9,'AbsTol',1e-11));
    V=evaluate_values_numeric(net,x',cfg.epsilon); dv=diff(V); viol=viol+sum(dv>2e-6); steps=steps+numel(dv); final(k)=norm(x(end,:)); data{k}=struct('t',t,'x',x,'V',V);
end
violRate=viol/max(1,steps); maxFinal=max(final);
end

function f=numeric_field(x,sys)
switch sys.type
    case "main", f=double(sys.A)*x+0.6*x(1)*double(sys.J*sys.P)*x;
    case "pendulum"
        u=double(sys.umax)*tanh((-double(sys.k1)*x(1)-double(sys.k2)*x(2))/double(sys.umax)); f=[x(2);sin(x(1))+u];
    case "oscillator4", f=[x(2);-2*x(1)-1.2*x(2)-0.2*x(1)^3+0.15*x(3);x(4);-1.5*x(3)-x(4)-0.15*x(3)^3+0.15*x(1)];
end
end

function V=evaluate_values_numeric(net,X,epsilon)
V=extractdata(positive_values(net,dlarray(single(X),"CB"),epsilon)); V=double(V(:));
end

function make_multiseed_figure(T,outDir)
fig=figure('Color','w','Position',[100 100 1250 520]); tl=tiledlayout(fig,1,3,'TileSpacing','compact','Padding','compact');
nexttile(tl); bar(T.Seed-20260825,T.PDERMSE,'FaceColor',[0.10 0.47 0.55]); grid on; xlabel('Independent run'); ylabel('PDE RMSE'); title('Ten-seed transport residual');
nexttile(tl); bar(T.Seed-20260825,T.MaxMarginRatio,'FaceColor',[0.72 0.25 0.18]); yline(0,'k--'); grid on; xlabel('Independent run'); ylabel('max m(x)/||x||^2'); title('Untouched-test decay margin');
nexttile(tl); bar(T.Seed-20260825,T.TrainingTime_s,'FaceColor',[0.30 0.45 0.72]); grid on; xlabel('Independent run'); ylabel('Training time (s)'); title(sprintf('Sampled gate success: %d/%d',sum(T.SampledGateSuccess),height(T)));
export_pair(fig,outDir,'fig08_multiseed_statistics'); close(fig);
end

function make_ablation_sensitivity_figure(A,S,outDir)
fig=figure('Color','w','Position',[100 100 1350 650]); tl=tiledlayout(fig,2,2,'TileSpacing','compact','Padding','compact');
nexttile(tl,[1 2]); yyaxis left; bar(categorical(A.Variant),A.MaxMarginRatio,'FaceColor',[0.18 0.47 0.67]); ylabel('max margin ratio'); yyaxis right; plot(categorical(A.Variant),A.PDERMSE,'o-','Color',[0.82 0.33 0.13]); ylabel('PDE RMSE'); grid on; title('Cumulative ablation at fixed optimization budget');
nexttile(tl); barh(categorical(S.Configuration),S.MaxMarginRatio,'FaceColor',[0.42 0.25 0.62]); xline(0,'k--'); grid on; xlabel('max margin ratio'); title('Sensitivity: certificate gate');
nexttile(tl); barh(categorical(S.Configuration),S.PDERMSE,'FaceColor',[0.12 0.55 0.42]); grid on; xlabel('PDE RMSE'); title('Sensitivity: transport fit');
export_pair(fig,outDir,'fig09_ablation_sensitivity'); close(fig);
end

function make_benchmark_figure(T,data,outDir)
fig=figure('Color','w','Position',[100 100 1300 680]); tl=tiledlayout(fig,2,2,'TileSpacing','compact','Padding','compact');
nexttile(tl); bar(categorical(T.Benchmark),T.MaxMarginRatio,'FaceColor',[0.19 0.45 0.68]); yline(0,'k--'); grid on; ylabel('max m/||x||^2'); title('Independent sampled certificate gate');
nexttile(tl); bar(categorical(T.Benchmark),T.PDERMSE,'FaceColor',[0.12 0.57 0.46]); grid on; ylabel('PDE RMSE'); title('Benchmark transport residual');
nexttile(tl); hold on; for k=1:numel(data{2}), x=data{2}{k}.x; plot(x(:,1),x(:,2)); end; grid on; xlabel('\theta');ylabel('\omega');title('Torque-saturated pendulum trajectories');
nexttile(tl); hold on; for k=1:numel(data{3}), d=data{3}{k}; semilogy(d.t,max(vecnorm(d.x,2,2),1e-12)); end; grid on; xlabel('Time');ylabel('||x(t)||_2');title('Four-state nonlinear oscillator decay');
export_pair(fig,outDir,'fig10_extended_benchmarks'); close(fig);
end

function export_pair(fig,outDir,name)
exportgraphics(fig,fullfile(outDir,name+".png"),'Resolution',320);
exportgraphics(fig,fullfile(outDir,name+".pdf"),'ContentType','vector');
end
