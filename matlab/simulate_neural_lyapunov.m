function simulate_neural_lyapunov(outDir)
% Public repository copy. Historical algorithm; see docs/VERIFICATION_STATUS.md.
% Fixed padding does not establish validated outward rounding.
% Reproducible experiments for the synthesized neural-Lyapunov manuscript.
% MATLAB R2024b, Deep Learning Toolbox, Control System Toolbox.

rng(20260826,"twister");
rootDir = fileparts(mfilename("fullpath"));
if nargin<1, outDir=fullfile(rootDir,"..","generated","base"); end
if ~exist(outDir,"dir")
    mkdir(outDir);
end

set(groot,"defaultAxesFontName","Arial");
set(groot,"defaultTextFontName","Arial");
set(groot,"defaultAxesFontSize",10);
set(groot,"defaultLineLineWidth",1.5);

fprintf("[1/7] Source-example consistency audit...\n");
audit = audit_source_example(outDir);

% Stable, nonlinear, non-normal benchmark. P solves A'P+PA=-I. The
% nonlinear term rho(x)JPx is energy-preserving with respect to x'Px.
A = [-1, 4; -0.5, -1];
P = lyap(A',eye(2));
J = [0, -1; 1, 0];
domainRadius = 2.0;
epsilonPD = 0.02;
decayRate = 0.15;

fprintf("[2/7] Supervised scalar-DNN baseline...\n");
[baselineNet,baseHistory,baseTrainTime] = train_supervised_baseline(P,domainRadius);

fprintf("[3/7] Structure-preserving neural Lyapunov model...\n");
[certificateNet,certHistory,certTrainTime,hardPoints] = ...
    train_structure_preserving(A,P,J,domainRadius,epsilonPD,decayRate);

fprintf("[4/7] Dense-grid and Monte-Carlo verification...\n");
[verification,gridData] = verify_models(baselineNet,certificateNet,A,P,J, ...
    domainRadius,epsilonPD,decayRate);

fprintf("[5/7] Closed-loop trajectories and robustness sweep...\n");
trajectory = trajectory_study(certificateNet,A,P,J,domainRadius,outDir);
robustness = robustness_study(certificateNet,A,P,J,domainRadius,decayRate,outDir);

fprintf("[6/7] Compositional scaling study...\n");
scaling = compositional_scaling(certificateNet,A,P,J,domainRadius,decayRate,outDir);

fprintf("[7/7] Publication-quality figures and result tables...\n");
make_workflow_figure(outDir);
make_training_figure(baseHistory,certHistory,outDir);
make_certificate_figure(gridData,hardPoints,outDir);

metrics = table( ...
    [baseTrainTime;certTrainTime], ...
    [verification.baseline.value_rel_l2;verification.proposed.value_rel_l2], ...
    [verification.baseline.value_rmse;verification.proposed.value_rmse], ...
    [verification.baseline.origin_abs;verification.proposed.origin_abs], ...
    [verification.baseline.min_value_outside_origin;verification.proposed.min_value_outside_origin], ...
    [verification.baseline.positive_definite_violation_rate;verification.proposed.positive_definite_violation_rate], ...
    [verification.baseline.derivative_violation_rate;verification.proposed.derivative_violation_rate], ...
    [verification.baseline.decay_margin_violation_rate;verification.proposed.decay_margin_violation_rate], ...
    [verification.baseline.max_decay_margin;verification.proposed.max_decay_margin], ...
    [verification.baseline.pde_rmse;verification.proposed.pde_rmse], ...
    'VariableNames',{'TrainingTime_s','RelativeL2ValueError','ValueRMSE', ...
    'AbsV0','MinimumValueOutsideOrigin','PositiveDefiniteViolationRate', ...
    'DerivativeViolationRate','DecayMarginViolationRate','MaximumDecayMargin','PDERMSE'}, ...
    'RowNames',{'Unconstrained_MSE_DNN','StructurePreserving_PDE_DNN'});
writetable(metrics,fullfile(outDir,"model_verification_metrics.csv"),"WriteRowNames",true);
writetable(struct2table(audit),fullfile(outDir,"source_example_audit.csv"));
writetable(struct2table(trajectory),fullfile(outDir,"trajectory_metrics.csv"));
writetable(struct2table(robustness),fullfile(outDir,"robustness_metrics.csv"));
writetable(struct2table(scaling),fullfile(outDir,"scaling_metrics.csv"));

save(fullfile(outDir,"neural_lyapunov_results.mat"),"A","P","J", ...
    "domainRadius","epsilonPD","decayRate","baselineNet","certificateNet", ...
    "baseHistory","certHistory","verification","audit","trajectory", ...
    "robustness","scaling");

fid = fopen(fullfile(outDir,"run_summary.txt"),"w");
fprintf(fid,"MATLAB version: %s\n",version);
fprintf(fid,"Random seed: 20260826\n");
fprintf(fid,"A = [%g %g; %g %g]\n",A(1,1),A(1,2),A(2,1),A(2,2));
fprintf(fid,"P = [%.12g %.12g; %.12g %.12g]\n",P(1,1),P(1,2),P(2,1),P(2,2));
fprintf(fid,"eig(P) = [%.12g %.12g]\n",eig(P));
fprintf(fid,"Lyapunov residual Frobenius norm = %.3e\n",norm(A'*P+P*A+eye(2),'fro'));
fprintf(fid,"Source example derivative violation rate = %.8f\n",audit.derivative_violation_rate);
fprintf(fid,"Baseline derivative violation rate = %.8f\n",verification.baseline.derivative_violation_rate);
fprintf(fid,"Proposed derivative violation rate = %.8f\n",verification.proposed.derivative_violation_rate);
fprintf(fid,"Proposed decay-margin violation rate = %.8f\n",verification.proposed.decay_margin_violation_rate);
fprintf(fid,"Proposed maximum decay margin = %.8e\n",verification.proposed.max_decay_margin);
fprintf(fid,"Trajectory monotonicity violation rate = %.8f\n",trajectory.monotonicity_violation_rate);
fprintf(fid,"Empirical robustness threshold = %.6f\n",robustness.empirical_zero_violation_delta(1));
fclose(fid);

disp(metrics);
fprintf("All outputs written to %s\n",outDir);
end


function audit = audit_source_example(outDir)
N = 250000;
X = 2*rand(4,N)-1;
Vdot = -4*X(1,:).^5 - 2*X(2,:).^2 - 6*X(3,:).^7 - 2*X(4,:).^2;
audit = struct;
audit.samples = N;
audit.derivative_violation_rate = mean(Vdot>0);
audit.maximum_orbital_derivative = max(Vdot);
audit.minimum_orbital_derivative = min(Vdot);
audit.example_negative_initial_state = -0.5;
audit.finite_escape_time = 2.0;

t = linspace(0,1.9,500);
x0 = -0.5;
xEven = x0./(1+x0*t);          % xdot=-x^2: finite escape at t=2.
xOdd = x0./sqrt(1+2*x0^2*t);   % xdot=-x^3: globally convergent.
vdEven = -4*xEven.^5;
vdOdd = -4*xOdd.^6;

fig = figure("Color","w","Position",[100 100 1180 470]);
tl = tiledlayout(fig,1,2,"TileSpacing","compact","Padding","compact");
nexttile(tl);
plot(t,xEven,"Color",[0.75 0.16 0.18],"DisplayName","Published even-power dynamics: dx/dt=-x^2"); hold on;
plot(t,xOdd,"Color",[0.08 0.45 0.45],"DisplayName","Corrected odd-power dynamics: dx/dt=-x^3");
yline(0,"k:","HandleVisibility","off"); grid on; xlabel("Time, t"); ylabel("State x_1(t)");
title("Negative initial state reveals finite escape"); legend("Location","southwest");
nexttile(tl);
plot(t,vdEven,"Color",[0.75 0.16 0.18],"DisplayName","dV/dt for even-power model"); hold on;
plot(t,vdOdd,"Color",[0.08 0.45 0.45],"DisplayName","dV/dt for corrected model");
yline(0,"k:","HandleVisibility","off"); grid on; xlabel("Time, t"); ylabel("Orbital derivative");
title("The claimed Lyapunov decrease fails for x_1<0"); legend("Location","northwest");
export_pair(fig,outDir,"fig02_source_example_audit");
close(fig);
end


function [net,history,elapsed] = train_supervised_baseline(P,R)
numTrain = 24000;
X = single((2*rand(2,numTrain)-1)*R);
Y = single(sum(X.*(P*X),1));
layers = [
    featureInputLayer(2,"Normalization","none","Name","state")
    fullyConnectedLayer(32,"Name","fc1")
    tanhLayer("Name","tanh1")
    fullyConnectedLayer(32,"Name","fc2")
    tanhLayer("Name","tanh2")
    fullyConnectedLayer(1,"Name","value")];
net = dlnetwork(layers);
avgGrad = [];
avgSqGrad = [];
iterations = 1400;
batchSize = 512;
history.iteration = (1:iterations)';
history.loss = zeros(iterations,1);
tic;
for iter = 1:iterations
    ids = randi(numTrain,1,batchSize);
    dlX = dlarray(X(:,ids),"CB");
    dlY = dlarray(Y(:,ids),"CB");
    [loss,gradients] = dlfeval(@baseline_loss,net,dlX,dlY);
    learnRate = 2e-3*(0.25+0.75*0.5*(1+cos(pi*(iter-1)/iterations)));
    [net,avgGrad,avgSqGrad] = adamupdate(net,gradients,avgGrad,avgSqGrad,iter,learnRate);
    history.loss(iter) = double(gather(extractdata(loss)));
    if mod(iter,350)==0
        fprintf("  baseline iteration %d/%d, loss %.3e\n",iter,iterations,history.loss(iter));
    end
end
elapsed = toc;
end


function [loss,gradients] = baseline_loss(net,X,Y)
prediction = forward(net,X);
loss = mean((prediction-Y).^2,"all");
gradients = dlgradient(loss,net.Learnables);
end


function [net,history,elapsed,hardPoints] = train_structure_preserving(A,P,J,R,epsilonPD,decayRate)
layers = [
    featureInputLayer(2,"Normalization","none","Name","state")
    fullyConnectedLayer(24,"Name","feature1")
    tanhLayer("Name","tanh1")
    fullyConnectedLayer(8,"Name","feature2")];
net = dlnetwork(layers);
net = scale_network_learnables(net,0.25);

iterations = 2200;
uniformBatch = 704;
nearBatch = 128;
hardBatch = 192;
hardPoints = single((2*rand(2,hardBatch)-1)*R);
history.iteration = (1:iterations)';
history.loss = zeros(iterations,1);
history.pde_rmse = zeros(iterations,1);
history.max_margin = zeros(iterations,1);
avgGrad = [];
avgSqGrad = [];
tic;
for iter = 1:iterations
    Xu = single((2*rand(2,uniformBatch)-1)*R);
    Xn = single(0.25*randn(2,nearBatch));
    Xn = max(min(Xn,R),-R);
    X = [Xu,Xn,hardPoints(:,randi(size(hardPoints,2),1,hardBatch))];
    dlX = dlarray(X,"CB");
    [loss,gradients,pdeRMSE,maxMargin] = dlfeval(@certificate_loss,net,dlX,A,P,J,epsilonPD,decayRate);
    learnRate = 1.5e-3*(0.2+0.8*0.5*(1+cos(pi*(iter-1)/iterations)));
    [net,avgGrad,avgSqGrad] = adamupdate(net,gradients,avgGrad,avgSqGrad,iter,learnRate);
    history.loss(iter) = double(gather(extractdata(loss)));
    history.pde_rmse(iter) = double(gather(extractdata(pdeRMSE)));
    history.max_margin(iter) = double(gather(extractdata(maxMargin)));

    if mod(iter,200)==0
        pool = single((2*rand(2,12000)-1)*R);
        [~,~,~,margin] = dlfeval(@certificate_quantities,net,dlarray(pool,"CB"),A,P,J,epsilonPD,decayRate,false);
        margin = gather(extractdata(margin));
        [~,idx] = maxk(margin,hardBatch);
        hardPoints = pool(:,idx);
        fprintf("  certificate iteration %d/%d, loss %.3e, max margin %.3e\n", ...
            iter,iterations,history.loss(iter),max(margin));
    end
end
elapsed = toc;
end


function net = scale_network_learnables(net,scale)
for i = 1:size(net.Learnables,1)
    value = net.Learnables.Value{i};
    if contains(net.Learnables.Parameter(i),"Weights")
        net.Learnables.Value{i} = value*scale;
    else
        net.Learnables.Value{i} = value*0;
    end
end
end


function [loss,gradients,pdeRMSE,maxMargin] = certificate_loss(net,X,A,P,J,epsilonPD,decayRate)
[V,dotV,norm2,margin] = certificate_quantities(net,X,A,P,J,epsilonPD,decayRate,true);
residual = (dotV+norm2)./(norm2+0.05);
scaledMargin = max(margin,0)./(norm2+0.05);

% A few exact PDE anchors remove the trajectory-wise additive ambiguity
% without changing the certificate conditions.
anchors = dlarray(single([1.5,-1.5,1.0,-1.0;1.0,-1.0,-1.5,1.5]),"CB");
Va = certificate_values(net,anchors,epsilonPD);
anchorsU = stripdims(anchors);
Vstar = sum(anchorsU.*(single(P)*anchorsU),1);
anchorLoss = mean(((Va-Vstar)./(Vstar+0.1)).^2,"all");

loss = mean(residual.^2,"all") + 8*mean(scaledMargin.^2,"all") + 0.05*anchorLoss;
gradients = dlgradient(loss,net.Learnables);
pdeRMSE = sqrt(mean((dotV+norm2).^2,"all"));
maxMargin = max(margin,[],"all");
end


function V = certificate_values(net,X,epsilonPD)
Xu = stripdims(X);
features = stripdims(forward(net,X));
zeroState = dlarray(zeros(2,1,"single"),"CB");
features0 = stripdims(forward(net,zeroState));
centered = features-features0;
V = epsilonPD*sum(Xu.^2,1)+sum(centered.^2,1);
end


function [V,dotV,norm2,margin,gradV] = certificate_quantities(net,X,A,P,J,epsilonPD,decayRate,higher)
V = certificate_values(net,X,epsilonPD);
gradV = stripdims(dlgradient(sum(V,"all"),X,"EnableHigherDerivatives",higher));
F = nonlinear_field(X,A,P,J);
dotV = sum(gradV.*F,1);
norm2 = sum(stripdims(X).^2,1);
margin = dotV+decayRate*norm2;
end


function [V,dotV,norm2,margin,gradV] = baseline_quantities(net,X,A,P,J,decayRate)
V = stripdims(forward(net,X));
gradV = stripdims(dlgradient(sum(V,"all"),X));
F = nonlinear_field(X,A,P,J);
dotV = sum(gradV.*F,1);
norm2 = sum(stripdims(X).^2,1);
margin = dotV+decayRate*norm2;
end


function F = nonlinear_field(X,A,P,J)
Xu = stripdims(X);
A = single(A); P = single(P); J = single(J);
PX = P*Xu;
rho = 0.6*Xu(1,:);
F = A*Xu + (J*PX).*rho;
end


function [verification,gridData] = verify_models(baseNet,certNet,A,P,J,R,epsilonPD,decayRate)
axisGrid = linspace(-R,R,181);
[X1,X2] = meshgrid(axisGrid,axisGrid);
Xgrid = single([X1(:)';X2(:)']);
Xrandom = single((2*rand(2,200000)-1)*R);
X = [Xgrid,Xrandom];
dlX = dlarray(X,"CB");
[Vb,dVb,n2b,mb] = dlfeval(@baseline_quantities,baseNet,dlX,A,P,J,decayRate);
[Vp,dVp,n2p,mp] = dlfeval(@certificate_quantities,certNet,dlX,A,P,J,epsilonPD,decayRate,false);

Vb = double(gather(extractdata(Vb)));
dVb = double(gather(extractdata(dVb)));
n2b = double(gather(extractdata(n2b)));
mb = double(gather(extractdata(mb)));
Vp = double(gather(extractdata(Vp)));
dVp = double(gather(extractdata(dVp)));
n2p = double(gather(extractdata(n2p)));
mp = double(gather(extractdata(mp)));
Xd = double(X);
Vexact = sum(Xd.*(P*Xd),1);
outside = n2b>1e-6;

verification.baseline = model_stats(Vb,dVb,n2b,mb,Vexact,outside);
verification.proposed = model_stats(Vp,dVp,n2p,mp,Vexact,outside);

ng = numel(X1);
gridData.X1 = X1;
gridData.X2 = X2;
gridData.Vexact = reshape(Vexact(1:ng),size(X1));
gridData.Vbaseline = reshape(Vb(1:ng),size(X1));
gridData.Vproposed = reshape(Vp(1:ng),size(X1));
gridData.dotProposed = reshape(dVp(1:ng),size(X1));
gridData.marginProposed = reshape(mp(1:ng),size(X1));
gridData.errorProposed = reshape(Vp(1:ng)-Vexact(1:ng),size(X1));
end


function stats = model_stats(V,dV,norm2,margin,Vexact,outside)
stats.value_rel_l2 = norm(V-Vexact)/norm(Vexact);
stats.value_rmse = sqrt(mean((V-Vexact).^2));
originMask = norm2<1e-12;
stats.origin_abs = min(abs(V(originMask)));
stats.min_value_outside_origin = min(V(outside));
stats.positive_definite_violation_rate = mean(V(outside)<=0);
stats.derivative_violation_rate = mean(dV(outside)>=0);
stats.decay_margin_violation_rate = mean(margin(outside)>=0);
stats.max_decay_margin = max(margin(outside));
stats.pde_rmse = sqrt(mean((dV+norm2).^2));
stats.minimum_normalized_decay = min(-dV(outside)./norm2(outside));
end


function trajectory = trajectory_study(net,A,P,J,R,outDir)
angles = linspace(0,2*pi,17); angles(end)=[];
initials = 0.55*R*[cos(angles);sin(angles)];
monotonicViolations = 0;
maxIncrease = 0;
finalNorms = zeros(1,size(initials,2));
trajectories = cell(1,size(initials,2));

for k = 1:size(initials,2)
    [t,x] = ode45(@(t,x) numeric_field(x,A,P,J),[0 12],initials(:,k), ...
        odeset("RelTol",1e-9,"AbsTol",1e-11));
    V = evaluate_certificate_values(net,x');
    dV = diff(V);
    monotonicViolations = monotonicViolations + nnz(dV>2e-6);
    maxIncrease = max(maxIncrease,max([0;dV(:)]));
    finalNorms(k) = norm(x(end,:));
    trajectories{k} = struct("t",t,"x",x,"V",V);
end

trajectory.number_of_initial_conditions = size(initials,2);
trajectory.total_time_steps = sum(cellfun(@(s)numel(s.t),trajectories));
trajectory.monotonicity_violation_rate = monotonicViolations/max(1,trajectory.total_time_steps-size(initials,2));
trajectory.maximum_single_step_value_increase = maxIncrease;
trajectory.maximum_final_state_norm = max(finalNorms);
trajectory.median_final_state_norm = median(finalNorms);

gridAxis = linspace(-R,R,161);
[X1,X2]=meshgrid(gridAxis,gridAxis);
Vgrid = reshape(evaluate_certificate_values(net,single([X1(:)';X2(:)'])),size(X1));

fig = figure("Color","w","Position",[100 100 1180 480]);
tl=tiledlayout(fig,1,2,"TileSpacing","compact","Padding","compact");
nexttile(tl);
contour(X1,X2,Vgrid,12,"Color",[0.72 0.76 0.82]); hold on;
colors=turbo(size(initials,2));
for k=1:size(initials,2)
    plot(trajectories{k}.x(:,1),trajectories{k}.x(:,2),"Color",colors(k,:));
end
plot(0,0,"kp","MarkerFaceColor","k","MarkerSize",9);
axis equal tight; grid on; xlabel("x_1"); ylabel("x_2");
title("Trajectories remain inside the verified domain");
nexttile(tl);
for k=1:4:size(initials,2)
    semilogy(trajectories{k}.t,max(trajectories{k}.V,1e-12),"Color",colors(k,:), ...
        "DisplayName",sprintf("x_0 angle %.0f deg",angles(k)*180/pi)); hold on;
end
grid on; xlabel("Time, t"); ylabel("V_\theta(x(t))");
title("Monotone certificate decay along trajectories"); legend("Location","southwest");
export_pair(fig,outDir,"fig05_trajectories_and_decay");
close(fig);
end


function V = evaluate_certificate_values(net,X)
if ~isa(X,"single"), X=single(X); end
V = gather(extractdata(dlfeval(@certificate_values,net,dlarray(X,"CB"),0.02)));
V = double(V(:));
end


function dx = numeric_field(x,A,P,J)
dx = A*x + 0.6*x(1)*(J*P*x);
end


function robustness = robustness_study(net,A,P,J,R,decayRate,outDir)
N = 80000;
X = single((2*rand(2,N)-1)*R);
dlX = dlarray(X,"CB");
[~,dNom,norm2,~,gradV] = dlfeval(@certificate_quantities,net,dlX,A,P,J,0.02,decayRate,false);
dNom = double(gather(extractdata(dNom)));
norm2 = double(gather(extractdata(norm2)));
G = double(gather(extractdata(gradV)));
Xd = double(X);
Bunc = [0.20,0.15;-0.10,0.25];
deltas = (0:0.1:1.6)';
violations = zeros(size(deltas));
maxMargins = zeros(size(deltas));
for i=1:numel(deltas)
    dPert = dNom + deltas(i)*sum(G.*(Bunc*Xd),1);
    margin = dPert + decayRate*norm2;
    violations(i) = mean(margin(norm2>1e-7)>=0);
    maxMargins(i) = max(margin(norm2>1e-7));
end
lastZero = find(violations==0,1,"last");
if isempty(lastZero), threshold=0; else, threshold=deltas(lastZero); end
alphaHat = min(-dNom(norm2>1e-5)./norm2(norm2>1e-5));
gradRatio = vecnorm(G(:,norm2>1e-5),2,1)./sqrt(norm2(norm2>1e-5));
analyticSampleBound = alphaHat/(max(gradRatio)*norm(Bunc,2));

robustness.delta = deltas;
robustness.violation_rate = violations;
robustness.maximum_margin = maxMargins;
robustness.empirical_zero_violation_delta = repmat(threshold,size(deltas));
robustness.sampled_alpha = repmat(alphaHat,size(deltas));
robustness.sampled_gradient_gain = repmat(max(gradRatio),size(deltas));
robustness.sampled_sufficient_delta_bound = repmat(analyticSampleBound,size(deltas));

fig=figure("Color","w","Position",[100 100 1120 460]);
tl=tiledlayout(fig,1,2,"TileSpacing","compact","Padding","compact");
nexttile(tl);
semilogy(deltas,max(violations,1/N),"o-","Color",[0.11 0.36 0.62],"MarkerFaceColor",[0.11 0.36 0.62]); hold on;
xline(analyticSampleBound,"--","Color",[0.78 0.39 0.08],"Label","sampled sufficient bound");
grid on; xlabel("Uncertainty scale, delta"); ylabel("Decay-margin violation rate");
title("Empirical robustness under Delta f=delta Bx");
nexttile(tl);
plot(deltas,maxMargins,"s-","Color",[0.56 0.18 0.55],"MarkerFaceColor",[0.56 0.18 0.55]); hold on;
yline(0,"k--"); grid on; xlabel("Uncertainty scale, delta"); ylabel("max [dV/dt + c||x||^2]");
title("Worst observed certificate margin");
export_pair(fig,outDir,"fig06_robustness_sweep");
close(fig);
end


function scaling = compositional_scaling(net,A,P,J,R,decayRate,outDir)
blocks = [1,2,4,8,16]';
dims = 2*blocks;
M = 12000;
kappa = 0.08;
evalTime = zeros(size(blocks));
violations = zeros(size(blocks));
maxMargin = zeros(size(blocks));
exactViolations = zeros(size(blocks));
for ib=1:numel(blocks)
    m=blocks(ib);
    X = single((2*rand(2,m,M)-1)*R);
    Z = reshape(X,2,[]);
    tic;
    [Vlocal,~,~,~,G] = dlfeval(@certificate_quantities,net,dlarray(Z,"CB"),A,P,J,0.02,decayRate,false);
    G = reshape(double(gather(extractdata(G))),2,m,M);
    Vlocal = reshape(double(gather(extractdata(Vlocal))),m,M);
    Xd = double(X);
    F = zeros(size(Xd));
    for i=1:m
        Zi = reshape(Xd(:,i,:),2,M);
        prev = reshape(Xd(:,mod(i-2,m)+1,:),2,M);
        F(:,i,:) = reshape(numeric_field_batch(Zi,A,P,J)+kappa*(prev-Zi),2,1,M);
    end
    dV = squeeze(sum(sum(G.*F,1),2));
    n2 = squeeze(sum(sum(Xd.^2,1),2));
    margin = dV + decayRate*n2;
    evalTime(ib)=toc;
    violations(ib)=mean(margin>=0);
    maxMargin(ib)=max(margin);
    exactD = exact_composite_derivative(Xd,P,kappa);
    exactViolations(ib)=mean(exactD>=0);
    %#ok<NASGU> Vlocal retains the compositional evaluation in the timed block.
end
gridCardinality = 21.^dims;
parameters = count_parameters(net);
scaling.state_dimension = dims;
scaling.subsystems = blocks;
scaling.samples = repmat(M,size(blocks));
scaling.shared_network_parameters = repmat(parameters,size(blocks));
scaling.evaluation_time_s = evalTime;
scaling.time_per_sample_ms = 1000*evalTime/M;
scaling.decay_margin_violation_rate = violations;
scaling.maximum_decay_margin = maxMargin;
scaling.exact_certificate_violation_rate = exactViolations;
scaling.tensor_grid_cardinality_21_per_axis = gridCardinality;

fig=figure("Color","w","Position",[100 100 1160 470]);
tl=tiledlayout(fig,1,2,"TileSpacing","compact","Padding","compact");
nexttile(tl);
yyaxis left;
plot(dims,1000*evalTime/M,"o-","Color",[0.12 0.42 0.55],"MarkerFaceColor",[0.12 0.42 0.55]);
ylabel("Evaluation time per sample (ms)");
yyaxis right;
plot(dims,log10(gridCardinality),"s--","Color",[0.75 0.30 0.12],"MarkerFaceColor",[0.75 0.30 0.12]);
ylabel("log10 tensor-grid points (21 per state)");
grid on; xlabel("State dimension"); title("Compositional evaluation versus tensor grids");
nexttile(tl);
semilogy(dims,max(violations,1/M),"o-","Color",[0.42 0.20 0.62],"MarkerFaceColor",[0.42 0.20 0.62]); hold on;
semilogy(dims,max(exactViolations,1/M),"s--","Color",[0.10 0.55 0.35],"MarkerFaceColor",[0.10 0.55 0.35]);
grid on; xlabel("State dimension"); ylabel("Decay-condition violation rate");
title(sprintf("Shared certificate: %d trainable parameters",parameters));
legend("Learned compositional V","Exact compositional V","Location","northwest");
export_pair(fig,outDir,"fig07_compositional_scaling");
close(fig);
end


function F = numeric_field_batch(X,A,P,J)
F = A*X + (J*P*X).*(0.6*X(1,:));
end


function dV = exact_composite_derivative(X,P,kappa)
[~,m,M]=size(X);
n2=squeeze(sum(sum(X.^2,1),2));
coupling=zeros(1,M);
for i=1:m
    Zi=reshape(X(:,i,:),2,M);
    prev=reshape(X(:,mod(i-2,m)+1,:),2,M);
    D=Zi-prev;
    coupling=coupling+kappa*sum(D.*(P*D),1);
end
dV=-n2-coupling(:);
end


function n = count_parameters(net)
n=0;
for i=1:size(net.Learnables,1)
    n=n+numel(net.Learnables.Value{i});
end
end


function make_workflow_figure(outDir)
fig=figure("Color","w","Position",[100 100 1300 610]);
ax=axes(fig,"Position",[0 0 1 1]); axis(ax,[0 1 0 1]); axis(ax,"off"); hold(ax,"on");
navy=[0.05 0.17 0.30]; teal=[0.05 0.48 0.50]; gold=[0.82 0.52 0.12];
fills={[0.91 0.94 0.97],[0.89 0.96 0.96],[0.98 0.94 0.85],[0.93 0.91 0.97],[0.91 0.96 0.92]};
boxes=[0.04 0.63 0.17 0.19;0.25 0.63 0.17 0.19;0.46 0.63 0.17 0.19;0.67 0.63 0.17 0.19;0.41 0.22 0.22 0.21];
titles={"1  Dynamics and controller","2  Positive architecture","3  Physics-informed loss","4  Counterexample mining","5  Verification and deployment"};
body={sprintf('Closed-loop f(x)\nEquilibrium and domain'), ...
    sprintf('Vtheta=eps||x||^2\n+||phi(x)-phi(0)||^2'), ...
    sprintf('Orbital derivative\nPDE residual and decay'), ...
    sprintf('Search hard states\nRetrain on violations'), ...
    sprintf('Grid + Monte Carlo +\nformal verifier interface')};
for i=1:5
    rectangle(ax,"Position",boxes(i,:),"Curvature",0.04,"FaceColor",fills{i},"EdgeColor",navy,"LineWidth",1.5);
    text(ax,boxes(i,1)+0.012,boxes(i,2)+boxes(i,4)-0.045,titles{i},"FontWeight","bold","Color",navy,"FontSize",11,"VerticalAlignment","top");
    text(ax,boxes(i,1)+boxes(i,3)/2,boxes(i,2)+0.075,body{i},"HorizontalAlignment","center","VerticalAlignment","middle","Color",[0.12 0.15 0.18],"FontSize",10,"Interpreter","none");
end
for i=1:3
    quiver(ax,boxes(i,1)+boxes(i,3)+0.01,0.725,boxes(i+1,1)-boxes(i,1)-boxes(i,3)-0.025,0,0,"Color",teal,"LineWidth",2,"MaxHeadSize",0.35);
end
quiver(ax,0.78,0.62,-0.22,-0.17,0,"Color",teal,"LineWidth",2,"MaxHeadSize",0.22);
quiver(ax,0.41,0.33,-0.18,0.22,0,"Color",gold,"LineWidth",2,"MaxHeadSize",0.22);
text(ax,0.29,0.43,"candidate rejected","Color",gold,"FontWeight","bold","Rotation",35,"HorizontalAlignment","center");
text(ax,0.52,0.12,"Accepted certificate feeds CLF-QP safety filters, adaptive control, observers, and ROA monitoring", ...
    "HorizontalAlignment","center","Color",navy,"FontWeight","bold","FontSize",11);
title(ax,"Structure-preserving neural Lyapunov synthesis and verification loop","Color",navy,"FontSize",16,"FontWeight","bold","Position",[0.5 0.94 0]);
export_pair(fig,outDir,"fig01_method_workflow");
close(fig);
end


function make_training_figure(baseHistory,certHistory,outDir)
fig=figure("Color","w","Position",[100 100 1180 470]);
tl=tiledlayout(fig,1,2,"TileSpacing","compact","Padding","compact");
nexttile(tl);
semilogy(baseHistory.iteration,movmean(baseHistory.loss,25),"Color",[0.75 0.25 0.18]); hold on;
semilogy(certHistory.iteration,movmean(certHistory.loss,25),"Color",[0.08 0.43 0.50]);
grid on; xlabel("Training iteration"); ylabel("Smoothed objective");
title("Regression loss versus certificate loss"); legend("MSE baseline","Structure-preserving PDE","Location","northeast");
nexttile(tl);
yyaxis left;
semilogy(certHistory.iteration,movmean(certHistory.pde_rmse,25),"Color",[0.12 0.40 0.65]);
ylabel("PDE residual RMSE");
yyaxis right;
plot(certHistory.iteration,movmax(certHistory.max_margin,25),"Color",[0.72 0.30 0.14]); hold on; yline(0,"k--");
ylabel("Worst mini-batch decay margin");
grid on; xlabel("Training iteration"); title("Physics residual and Lyapunov decrease");
export_pair(fig,outDir,"fig03_training_convergence");
close(fig);
end


function make_certificate_figure(g,hardPoints,outDir)
fig=figure("Color","w","Position",[100 100 1180 900]);
tl=tiledlayout(fig,2,2,"TileSpacing","compact","Padding","compact");
nexttile(tl); contourf(g.X1,g.X2,g.Vexact,30,"LineColor","none"); axis equal tight; colorbar; xlabel("x_1"); ylabel("x_2"); title("Exact V*(x)=x^T P x");
nexttile(tl); contourf(g.X1,g.X2,g.Vproposed,30,"LineColor","none"); axis equal tight; colorbar; xlabel("x_1"); ylabel("x_2"); title("Learned positive-definite V_theta");
nexttile(tl); contourf(g.X1,g.X2,g.errorProposed,30,"LineColor","none"); axis equal tight; colorbar; xlabel("x_1"); ylabel("x_2"); title("Approximation error V_theta-V*");
nexttile(tl); contourf(g.X1,g.X2,g.marginProposed,30,"LineColor","none"); hold on; scatter(hardPoints(1,:),hardPoints(2,:),8,"k","filled","MarkerFaceAlpha",0.28); axis equal tight; colorbar; xlabel("x_1"); ylabel("x_2"); title("Decay margin dV/dt+c||x||^2 (hard points overlaid)");
colormap(fig,turbo(256));
export_pair(fig,outDir,"fig04_learned_certificate_fields");
close(fig);
end


function export_pair(fig,outDir,stem)
axs = findall(fig,"Type","axes");
for k = 1:numel(axs)
    disableDefaultInteractivity(axs(k));
    axtoolbar(axs(k),"Visible","off");
end
exportgraphics(fig,fullfile(outDir,stem+".png"),"Resolution",400,"BackgroundColor","white");
exportgraphics(fig,fullfile(outDir,stem+".pdf"),"ContentType","vector","BackgroundColor","white");
end
