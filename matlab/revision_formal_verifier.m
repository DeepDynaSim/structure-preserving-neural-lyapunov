function revision_formal_verifier(inputFile,outDir)
% Public repository copy. Historical algorithm; see docs/VERIFICATION_STATUS.md.
% Fixed padding does not establish validated outward rounding.
% Conservative interval/Jacobian verification for the selected no-anchor
% structure-preserving neural Lyapunov certificate. The script exports the
% exact network, dynamics, solver settings, partition, and derived bounds.

rootDir=fileparts(mfilename("fullpath"));
if nargin<1, inputFile=fullfile(rootDir,"..","results","revision","revision_experiments.mat"); end
if nargin<2, outDir=fullfile(rootDir,"..","generated","guarded_verification"); end
if ~exist(outDir,"dir"), mkdir(outDir); end
warning("Lyapunov:NotValidated","Fixed floating-point padding is NOT validated outward rounding. Outputs are numerical targets, not formal certificates.");
S = load(inputFile,"chosenNet","chosenSeed","sys","cfg");
net = S.chosenNet;
A = double(S.sys.A); P = double(S.sys.P); J = double(S.sys.J);
epsilon = double(S.cfg.epsilon); c = double(S.cfg.decay);

W1 = learnable(net,"feature1","Weights");
b1 = learnable(net,"feature1","Bias");
W2 = learnable(net,"feature2","Weights");
b2 = learnable(net,"feature2","Bias");

domainRadius = 2.0;
minimumWidth = 2^-12;
roundingGuard = 1e-12;
radii = [0.01 0.02 0.05 0.1 0.2 0.3 0.4 0.5 0.75 1.0 1.5 2.0];
radiusTable = zeros(numel(radii),5);
for i = 1:numel(radii)
    R = radii(i);
    [lambdaUpper,alphaLower,gradGain,bUpper] = ...
        global_matrix_bound(W1,b1,W2,A,P,J,epsilon,c,R);
    radiusTable(i,:) = [R,lambdaUpper,alphaLower,gradGain,bUpper];
end
radiusTable = array2table(radiusTable,"VariableNames", ...
    ["Radius","LambdaUpperWithDecay","NominalAlphaLower","GradientGainUpper","ValueUpperCoefficient"]);
writetable(radiusTable,fullfile(outDir,"formal_local_radius_scan.csv"));

eligible = radiusTable.Radius(radiusTable.LambdaUpperWithDecay < -1e-10);
assert(~isempty(eligible),"No local matrix certificate was found.");
localRadius = max(eligible);
localRow = radiusTable(radiusTable.Radius==localRadius,:);

[stats,acceptedBoxes] = verify_domain_bab(W1,b1,W2,A,P,J,epsilon,c, ...
    domainRadius,localRadius,minimumWidth);
assert(stats.UnresolvedBoxes==0,"Interval verification left unresolved boxes.");

[~,~,globalGradientGain,globalValueUpper] = ...
    global_matrix_bound(W1,b1,W2,A,P,J,epsilon,0,domainRadius);
Bperturb = [0.20 0.15;-0.10 0.25];
perturbationNorm = norm(Bperturb,2);
deltaCertified = c/(globalGradientGain*perturbationNorm);
rhoCertified = 0.04;
boundaryLower = epsilon*domainRadius^2;
stateGain = sqrt(globalValueUpper/epsilon);
stateExponent = c/(2*globalValueUpper);
kappaMaximum = c/(2*globalGradientGain);
kappaUsed = 0.01;
compositionalDecay = c-2*kappaUsed*globalGradientGain;

metricNames = [ ...
    "SelectedSeed";"DomainRadius";"DecayRate";"PositiveQuadraticFloor"; ...
    "LocalCertifiedRadius";"LocalLambdaUpperWithDecay";"LocalNominalAlphaLower"; ...
    "LocalGradientGainUpper";"GlobalGradientGainUpper";"GlobalValueUpperCoefficient"; ...
    "ExploredBoxes";"LocalBoxes";"DirectIntervalBoxes";"UnresolvedBoxes"; ...
    "MaximumDepth";"MinimumBoxWidth";"ClosestDirectCertifiedUpper";"VerificationTimeSeconds"; ...
    "ROALevelRho";"BoundaryValueLower";"ExponentialStateGain";"ExponentialStateExponent"; ...
    "PerturbationMatrixSpectralNorm";"CertifiedPerturbationDelta"; ...
    "CompositionalKappaMaximum";"CompositionalKappaUsed";"CompositionalDecayMargin"; ...
    "RoundingGuard"];
metricValues = [ ...
    double(S.chosenSeed);domainRadius;c;epsilon;localRadius; ...
    localRow.LambdaUpperWithDecay;localRow.NominalAlphaLower;localRow.GradientGainUpper; ...
    globalGradientGain;globalValueUpper;stats.ExploredBoxes;stats.LocalBoxes; ...
    stats.DirectIntervalBoxes;stats.UnresolvedBoxes;stats.MaximumDepth;minimumWidth; ...
    stats.ClosestDirectCertifiedUpper;stats.ElapsedSeconds;rhoCertified;boundaryLower; ...
    stateGain;stateExponent;perturbationNorm;deltaCertified;kappaMaximum;kappaUsed; ...
    compositionalDecay;roundingGuard];
metricValues = metricValues(:);
metrics = table(metricNames,metricValues,'VariableNames',{'Metric','Value'});
writetable(metrics,fullfile(outDir,"formal_verification_metrics.csv"));

boxTable = array2table(acceptedBoxes,"VariableNames", ...
    ["LowerX1","LowerX2","UpperX1","UpperX2","Depth","MethodCode","MarginUpper"]);
writetable(boxTable,fullfile(outDir,"formal_verified_partition.csv"));

writematrix(A,fullfile(outDir,"dynamics_A.csv"));
writematrix(P,fullfile(outDir,"dynamics_P.csv"));
writematrix(J,fullfile(outDir,"dynamics_J.csv"));
writematrix(Bperturb,fullfile(outDir,"perturbation_B.csv"));
writematrix(W1,fullfile(outDir,"network_W1.csv"));
writematrix(b1,fullfile(outDir,"network_b1.csv"));
writematrix(W2,fullfile(outDir,"network_W2.csv"));
writematrix(b2,fullfile(outDir,"network_b2.csv"));
save(fullfile(outDir,"certified_network_and_dynamics.mat"), ...
    "W1","b1","W2","b2","A","P","J","Bperturb","epsilon","c", ...
    "domainRadius","localRadius","minimumWidth","roundingGuard","metrics","boxTable");

write_log(fullfile(outDir,"formal_verification_log.txt"),S.chosenSeed,stats, ...
    localRadius,localRow,globalGradientGain,globalValueUpper,rhoCertified, ...
    boundaryLower,deltaCertified,kappaMaximum,kappaUsed,compositionalDecay,minimumWidth,roundingGuard);
plot_partition(acceptedBoxes,domainRadius,localRadius,fullfile(outDir,"fig11_interval_verification"));
plot_candidate_fields(W1,b1,W2,A,P,J,epsilon,c,domainRadius,rhoCertified, ...
    fullfile(outDir,"fig12_certified_candidate_fields"));

fprintf("Guarded numerical calculation complete: explored=%d, unresolved=%d, elapsed=%.3f s.\n", ...
    stats.ExploredBoxes,stats.UnresolvedBoxes,stats.ElapsedSeconds);
fprintf("Numerical target delta=%.9g, kappa_max=%.9g, global g=%.9g, global b=%.9g.\n", ...
    deltaCertified,kappaMaximum,globalGradientGain,globalValueUpper);
end

function value = learnable(net,layerName,paramName)
idx = net.Learnables.Layer==layerName & net.Learnables.Parameter==paramName;
assert(nnz(idx)==1,"Missing or duplicate learnable parameter.");
value = double(gather(extractdata(net.Learnables.Value{idx})));
end

function [lambdaUpper,alphaLower,gradGain,bUpper] = global_matrix_bound(W1,b1,W2,A,P,J,epsilon,c,R)
zrad = R*sum(abs(W1),2);
zlo = b1-zrad; zhi = b1+zrad;
dlo = zeros(size(zlo)); dhi = zeros(size(zlo));
for k=1:numel(zlo)
    vals = [sech(zlo(k))^2,sech(zhi(k))^2];
    dlo(k)=min(vals);
    if zlo(k)<=0 && zhi(k)>=0, dhi(k)=1; else, dhi(k)=max(vals); end
end
[Jlo,Jhi] = scalar_sum_outer_interval(W2,W1,dlo,dhi);
[Jlo,Jhi] = outward(Jlo,Jhi);
[Klo,Khi] = interval_matmul(Jlo',Jhi',Jlo,Jhi);
Glo = 2*Klo; Ghi = 2*Khi;
Glo(1,1)=Glo(1,1)+2*epsilon; Ghi(1,1)=Ghi(1,1)+2*epsilon;
Glo(2,2)=Glo(2,2)+2*epsilon; Ghi(2,2)=Ghi(2,2)+2*epsilon;
[Glo,Ghi]=outward(Glo,Ghi);

JP = J*P;
Flo = A-0.6*R*abs(JP); Fhi = A+0.6*R*abs(JP);
[Flo,Fhi]=outward(Flo,Fhi);
[Mlo,Mhi] = interval_matmul(Glo',Ghi',Flo,Fhi);
Mlo(1,1)=Mlo(1,1)+c; Mhi(1,1)=Mhi(1,1)+c;
Mlo(2,2)=Mlo(2,2)+c; Mhi(2,2)=Mhi(2,2)+c;
[Slo,Shi] = sym_interval(Mlo,Mhi);
lambdaUpper = symmetric_interval_lambda_upper(Slo,Shi);
Nlo=Mlo; Nhi=Mhi;
Nlo(1,1)=Nlo(1,1)-c; Nhi(1,1)=Nhi(1,1)-c;
Nlo(2,2)=Nlo(2,2)-c; Nhi(2,2)=Nhi(2,2)-c;
[Nsl,Nsu]=sym_interval(Nlo,Nhi);
alphaLower=-symmetric_interval_lambda_upper(Nsl,Nsu);
gradGain = interval_spectral_norm_upper(Glo,Ghi);
bnorm = interval_spectral_norm_upper(Jlo,Jhi);
bUpper = epsilon+bnorm^2;
end

function [lo,hi] = scalar_sum_outer_interval(W2,W1,dlo,dhi)
lo=zeros(size(W2,1),size(W1,2)); hi=lo;
for k=1:size(W1,1)
    C=W2(:,k)*W1(k,:); a=C*dlo(k); b=C*dhi(k);
    lo=lo+min(a,b); hi=hi+max(a,b);
end
end

function [Clo,Chi] = interval_matmul(Alo,Ahi,Blo,Bhi)
Clo=zeros(size(Alo,1),size(Blo,2)); Chi=Clo;
for i=1:size(Alo,1)
    for j=1:size(Blo,2)
        for k=1:size(Alo,2)
            vals=[Alo(i,k)*Blo(k,j),Alo(i,k)*Bhi(k,j),Ahi(i,k)*Blo(k,j),Ahi(i,k)*Bhi(k,j)];
            Clo(i,j)=Clo(i,j)+min(vals); Chi(i,j)=Chi(i,j)+max(vals);
        end
    end
end
[Clo,Chi]=outward(Clo,Chi);
end

function [Slo,Shi] = sym_interval(Mlo,Mhi)
Slo=(Mlo+Mlo')/2; Shi=(Mhi+Mhi')/2; [Slo,Shi]=outward(Slo,Shi);
end

function ub = symmetric_interval_lambda_upper(lo,hi)
ub=-inf;
for i=1:size(lo,1)
    radius=0;
    for j=1:size(lo,2)
        if i~=j, radius=radius+max(abs([lo(i,j),hi(i,j)])); end
    end
    ub=max(ub,hi(i,i)+radius);
end
ub=ub+1e-12*(1+abs(ub));
end

function ub = interval_spectral_norm_upper(lo,hi)
M=max(abs(lo),abs(hi)); ub=sqrt(norm(M,1)*norm(M,inf));
ub=ub+1e-12*(1+abs(ub));
end

function [stats,accepted] = verify_domain_bab(W1,b1,W2,A,P,J,epsilon,c,R,localR,minWidth)
stack=[-R,-R,R,R,0]; accepted=zeros(0,7);
explored=0; localBoxes=0; directBoxes=0; unresolved=0; maxDepth=0;
closestDirect=-inf; tic;
while ~isempty(stack)
    box=stack(end,:); stack(end,:)=[]; explored=explored+1;
    lo=box(1:2)'; hi=box(3:4)'; depth=box(5); maxDepth=max(maxDepth,depth);
    if all(lo>=-localR) && all(hi<=localR)
        localBoxes=localBoxes+1;
        accepted(end+1,:)=[box,1,NaN]; %#ok<AGROW>
        continue
    end
    [~,mhi]=direct_margin_interval(W1,b1,W2,A,P,J,epsilon,c,lo,hi);
    if mhi < -1e-10
        directBoxes=directBoxes+1; closestDirect=max(closestDirect,mhi);
        accepted(end+1,:)=[box,2,mhi]; %#ok<AGROW>
        continue
    end
    widths=hi-lo;
    if max(widths)<=minWidth
        unresolved=unresolved+1;
        accepted(end+1,:)=[box,0,mhi]; %#ok<AGROW>
        continue
    end
    [~,k]=max(widths); mid=(lo(k)+hi(k))/2;
    hi1=hi; hi1(k)=mid; lo2=lo; lo2(k)=mid;
    stack=[stack;lo(1),lo(2),hi1(1),hi1(2),depth+1; ...
        lo2(1),lo2(2),hi(1),hi(2),depth+1]; %#ok<AGROW>
end
stats=struct("ExploredBoxes",explored,"LocalBoxes",localBoxes, ...
    "DirectIntervalBoxes",directBoxes,"UnresolvedBoxes",unresolved, ...
    "MaximumDepth",maxDepth,"ClosestDirectCertifiedUpper",closestDirect, ...
    "ElapsedSeconds",toc);
end

function [mlo,mhi] = direct_margin_interval(W1,b1,W2,A,P,J,epsilon,c,xlo,xhi)
[zlo,zhi]=linear_interval(W1,xlo,xhi,b1);
tlo=tanh(zlo); thi=tanh(zhi); [tlo,thi]=outward(tlo,thi);
[philo,phihi]=linear_interval(W2,tlo,thi,zeros(size(W2,1),1));
phi0=W2*tanh(b1);
glo=philo-phi0; ghi=phihi-phi0; [glo,ghi]=outward(glo,ghi);
dlo=zeros(size(zlo)); dhi=dlo;
for k=1:numel(zlo)
    vals=[sech(zlo(k))^2,sech(zhi(k))^2]; dlo(k)=min(vals);
    if zlo(k)<=0 && zhi(k)>=0, dhi(k)=1; else, dhi(k)=max(vals); end
end
[Jlo,Jhi]=scalar_sum_outer_interval(W2,W1,dlo,dhi); [Jlo,Jhi]=outward(Jlo,Jhi);
[qlo,qhi]=interval_matvec(Jlo',Jhi',glo,ghi);
gradlo=2*epsilon*xlo+2*qlo; gradhi=2*epsilon*xhi+2*qhi; [gradlo,gradhi]=outward(gradlo,gradhi);
[Alo,Ahi]=linear_interval(A,xlo,xhi,zeros(2,1));
[ylo,yhi]=linear_interval(J*P,xlo,xhi,zeros(2,1));
[nlo,nhi]=interval_scalar_times_vector(xlo(1),xhi(1),ylo,yhi);
flo=Alo+0.6*nlo; fhi=Ahi+0.6*nhi; [flo,fhi]=outward(flo,fhi);
[dotlo,dothi]=interval_dot(gradlo,gradhi,flo,fhi);
[slo,shi]=square_interval(xlo,xhi);
mlo=dotlo+c*sum(slo); mhi=dothi+c*sum(shi); [mlo,mhi]=outward(mlo,mhi);
end

function [lo,hi]=linear_interval(W,xlo,xhi,b)
Wp=max(W,0); Wn=min(W,0);
lo=Wp*xlo+Wn*xhi+b; hi=Wp*xhi+Wn*xlo+b; [lo,hi]=outward(lo,hi);
end

function [lo,hi]=interval_matvec(Alo,Ahi,xlo,xhi)
lo=zeros(size(Alo,1),1); hi=lo;
for i=1:size(Alo,1)
    for k=1:size(Alo,2)
        vals=[Alo(i,k)*xlo(k),Alo(i,k)*xhi(k),Ahi(i,k)*xlo(k),Ahi(i,k)*xhi(k)];
        lo(i)=lo(i)+min(vals); hi(i)=hi(i)+max(vals);
    end
end
[lo,hi]=outward(lo,hi);
end

function [lo,hi]=interval_scalar_times_vector(alo,ahi,blo,bhi)
lo=zeros(size(blo)); hi=lo;
for k=1:numel(blo)
    vals=[alo*blo(k),alo*bhi(k),ahi*blo(k),ahi*bhi(k)]; lo(k)=min(vals); hi(k)=max(vals);
end
[lo,hi]=outward(lo,hi);
end

function [lo,hi]=interval_dot(alo,ahi,blo,bhi)
lo=0; hi=0;
for k=1:numel(alo)
    vals=[alo(k)*blo(k),alo(k)*bhi(k),ahi(k)*blo(k),ahi(k)*bhi(k)];
    lo=lo+min(vals); hi=hi+max(vals);
end
[lo,hi]=outward(lo,hi);
end

function [lo,hi]=square_interval(xlo,xhi)
lo=zeros(size(xlo)); hi=lo;
for k=1:numel(xlo)
    hi(k)=max(xlo(k)^2,xhi(k)^2);
    if xlo(k)<=0 && xhi(k)>=0, lo(k)=0; else, lo(k)=min(xlo(k)^2,xhi(k)^2); end
end
[lo,hi]=outward(lo,hi);
end

function [lo,hi]=outward(lo,hi)
inflate=1e-12*(1+max(abs(lo),abs(hi))); lo=lo-inflate; hi=hi+inflate;
end

function write_log(path,seed,stats,localRadius,localRow,g,b,rho,boundaryLower,delta,kmax,kused,kdecay,minWidth,guard)
fid=fopen(path,'w'); cleanup=onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,"Selected no-anchor seed: %d\n",seed);
fprintf(fid,"Verifier: conservative interval/Jacobian branch-and-bound; IEEE-754 double with %.3g outward guard per primitive\n",guard);
fprintf(fid,"Domain: [-2,2]^2; target: dot(V)+0.15||x||^2 <= 0; acceptance tolerance: upper bound < -1e-10\n");
fprintf(fid,"Local matrix square: [-%.9g,%.9g]^2; lambda upper %.12g; nominal alpha lower %.12g\n", ...
    localRadius,localRadius,localRow.LambdaUpperWithDecay,localRow.NominalAlphaLower);
fprintf(fid,"Branch-and-bound: explored %d; local %d; direct %d; unresolved %d; max depth %d; min width %.12g; elapsed %.6f s\n", ...
    stats.ExploredBoxes,stats.LocalBoxes,stats.DirectIntervalBoxes,stats.UnresolvedBoxes,stats.MaximumDepth,minWidth,stats.ElapsedSeconds);
fprintf(fid,"Closest accepted direct interval upper bound: %.12g\n",stats.ClosestDirectCertifiedUpper);
fprintf(fid,"Global gradient gain g <= %.12g; V upper coefficient b <= %.12g\n",g,b);
fprintf(fid,"Certified ROA rho %.12g; boundary V lower %.12g\n",rho,boundaryLower);
fprintf(fid,"Certified structured perturbation delta < %.12g\n",delta);
fprintf(fid,"Learned interconnection small-gain: kappa < %.12g; tested formal kappa %.12g; decay margin %.12g\n",kmax,kused,kdecay);
fprintf(fid,"Network and dynamics are exported in CSV and MAT files; partition is exported in formal_verified_partition.csv.\n");
end

function plot_partition(boxes,R,localR,outBase)
direct=boxes(boxes(:,6)==2,:); local=boxes(boxes(:,6)==1,:);
fig=figure("Color","w","Position",[100 100 1700 760]);
tiledlayout(1,2,"Padding","compact","TileSpacing","compact");
nexttile; hold on;
if ~isempty(direct), draw_boxes(direct,[0.16 0.55 0.75],0.78); end
if ~isempty(local), draw_boxes(local,[0.93 0.45 0.16],0.90); end
rectangle("Position",[-localR,-localR,2*localR,2*localR],"EdgeColor","k","LineWidth",1.5);
axis equal tight; xlim([-R R]); ylim([-R R]); grid on; box on;
xlabel("x_1"); ylabel("x_2"); title("Certified interval partition");
legend([plot(nan,nan,'s','MarkerFaceColor',[0.16 0.55 0.75],'MarkerEdgeColor','none'), ...
    plot(nan,nan,'s','MarkerFaceColor',[0.93 0.45 0.16],'MarkerEdgeColor','none')], ...
    ["direct interval bound","local matrix bound"],"Location","southoutside","Orientation","horizontal");

nexttile;
scatter(direct(:,5),direct(:,7),18,direct(:,5),'filled','MarkerFaceAlpha',0.55); hold on;
yline(-1e-10,'k--','acceptance threshold'); grid on; box on;
xlabel("branch depth"); ylabel("upper bound on dot(V)+c||x||^2");
title("Accepted direct boxes (all bounds negative)"); colorbar;
exportgraphics(fig,outBase+".png","Resolution",360);
exportgraphics(fig,outBase+".pdf","ContentType","vector"); close(fig);
end

function draw_boxes(boxes,color,alpha)
n=size(boxes,1); X=zeros(5,n); Y=zeros(5,n);
for i=1:n
    lo=boxes(i,1:2); hi=boxes(i,3:4);
    X(:,i)=[lo(1);hi(1);hi(1);lo(1);lo(1)];
    Y(:,i)=[lo(2);lo(2);hi(2);hi(2);lo(2)];
end
patch(X,Y,zeros(size(X)),"FaceColor",color,"EdgeColor","none","FaceAlpha",alpha);
end

function plot_candidate_fields(W1,b1,W2,A,P,J,epsilon,c,R,rho,outBase)
v=linspace(-R,R,241); [X1,X2]=meshgrid(v,v); X=[X1(:)';X2(:)'];
H=tanh(W1*X+b1); phi=W2*H; phi0=W2*tanh(b1); dphi=phi-phi0;
V=epsilon*sum(X.^2,1)+sum(dphi.^2,1);
back=(1-H.^2).*(W2'*dphi); grad=2*epsilon*X+2*W1'*back;
PX=P*X; F=A*X+0.6*X(1,:).*(J*PX);
margin=sum(grad.*F,1)+c*sum(X.^2,1);
Vexact=sum(X.*PX,1);
V=reshape(V,size(X1)); margin=reshape(margin,size(X1)); Vexact=reshape(Vexact,size(X1));

fig=figure("Color","w","Position",[100 100 1950 650]);
tiledlayout(1,3,"Padding","compact","TileSpacing","compact");
nexttile; contourf(X1,X2,V,24,"LineColor","none"); hold on;
contour(X1,X2,V,[rho rho],"k","LineWidth",2.2); axis equal tight; grid on; box on;
xlabel("x_1"); ylabel("x_2"); title(sprintf("Neural V and certified \\rho=%.2f",rho)); colorbar;
nexttile; imagesc(v,v,margin); axis xy equal tight; grid on; box on;
xlabel("x_1"); ylabel("x_2"); title("Sampled decay margin (formal bound: entire square)");
clim([min(margin,[],'all') 0]); colorbar;
nexttile; contour(X1,X2,Vexact,12,"Color",[0.05 0.25 0.55],"LineWidth",1.3); hold on;
contour(X1,X2,V,12,"--","Color",[0.85 0.25 0.12],"LineWidth",1.2);
axis equal tight; grid on; box on; xlabel("x_1"); ylabel("x_2");
title("Exact and learned level sets");
legend([plot(nan,nan,'-','Color',[0.05 0.25 0.55],'LineWidth',1.3), ...
    plot(nan,nan,'--','Color',[0.85 0.25 0.12],'LineWidth',1.2)], ...
    ["exact quadratic","learned certificate"],"Location","southoutside","Orientation","horizontal");
exportgraphics(fig,outBase+".png","Resolution",360);
exportgraphics(fig,outBase+".pdf","ContentType","vector"); close(fig);
end
