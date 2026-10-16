function formal_verify_neural
% Sound but conservative interval/Jacobian verification prototype for the
% learned structure-preserving tanh certificate.

S = load('neural_lyapunov_results.mat');
net = S.certificateNet;
A = double(S.A); P = double(S.P); J = double(S.J);
epsilon = double(S.epsilonPD); c = double(S.decayRate);

W1 = learnable(net,"feature1","Weights");
b1 = learnable(net,"feature1","Bias");
W2 = learnable(net,"feature2","Weights");

radii = [0.01 0.02 0.05 0.1 0.2 0.3 0.4 0.5 0.75 1.0 1.5 2.0];
fprintf('R,lambda_upper,alpha_lower,grad_gain_upper,b_upper\n');
for R = radii
    [lambdaUpper,alphaLower,gradGain,bUpper] = global_matrix_bound(W1,b1,W2,A,P,J,epsilon,c,R);
    fprintf('%.5g,%.9g,%.9g,%.9g,%.9g\n',R,lambdaUpper,alphaLower,gradGain,bUpper);
end

fprintf('\nAdaptive interval branch-and-bound on [-2,2]^2\n');
verify_domain_bab(W1,b1,W2,A,P,J,epsilon,c,2.0,0.2,2^-12);
end

function value = learnable(net,layerName,paramName)
idx = net.Learnables.Layer==layerName & net.Learnables.Parameter==paramName;
value = double(extractdata(net.Learnables.Value{idx}));
end

function [lambdaUpper,alphaLower,gradGain,bUpper] = global_matrix_bound(W1,b1,W2,A,P,J,epsilon,c,R)
% Bound the hidden activation derivative over [-R,R]^2.
zrad = R*sum(abs(W1),2);
zlo = b1-zrad; zhi = b1+zrad;
dlo = zeros(size(zlo)); dhi = zeros(size(zlo));
for k=1:numel(zlo)
    vals = [sech(zlo(k))^2,sech(zhi(k))^2];
    dlo(k)=min(vals);
    if zlo(k)<=0 && zhi(k)>=0
        dhi(k)=1;
    else
        dhi(k)=max(vals);
    end
end

% Interval Jphi = sum_h W2(:,h)*W1(h,:)*d_h.
[Jlo,Jhi] = scalar_sum_outer_interval(W2,W1,dlo,dhi);

% g(x)=phi(x)-phi(0)=B(x)x with B in the same Jacobian interval by the
% integral mean-value representation. grad V = G(x)x.
[Klo,Khi] = interval_matmul(Jlo',Jhi',Jlo,Jhi);
Glo = 2*Klo; Ghi = 2*Khi;
Glo(1,1)=Glo(1,1)+2*epsilon; Ghi(1,1)=Ghi(1,1)+2*epsilon;
Glo(2,2)=Glo(2,2)+2*epsilon; Ghi(2,2)=Ghi(2,2)+2*epsilon;

JP = J*P;
Flo = A-0.6*R*abs(JP);
Fhi = A+0.6*R*abs(JP);

[Mlo,Mhi] = interval_matmul(Glo',Ghi',Flo,Fhi);
Mlo(1,1)=Mlo(1,1)+c; Mhi(1,1)=Mhi(1,1)+c;
Mlo(2,2)=Mlo(2,2)+c; Mhi(2,2)=Mhi(2,2)+c;
[Slo,Shi] = sym_interval(Mlo,Mhi);
lambdaUpper = symmetric_interval_lambda_upper(Slo,Shi);

% Nominal (without +cI) certified decay alpha and gradient/value bounds.
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
    C=W2(:,k)*W1(k,:);
    a=C*dlo(k); b=C*dhi(k);
    lo=lo+min(a,b); hi=hi+max(a,b);
end
end

function [Clo,Chi] = interval_matmul(Alo,Ahi,Blo,Bhi)
Clo=zeros(size(Alo,1),size(Blo,2)); Chi=Clo;
for i=1:size(Alo,1)
    for j=1:size(Blo,2)
        for k=1:size(Alo,2)
            vals=[Alo(i,k)*Blo(k,j),Alo(i,k)*Bhi(k,j),Ahi(i,k)*Blo(k,j),Ahi(i,k)*Bhi(k,j)];
            Clo(i,j)=Clo(i,j)+min(vals);
            Chi(i,j)=Chi(i,j)+max(vals);
        end
    end
end
end

function [Slo,Shi] = sym_interval(Mlo,Mhi)
Slo=(Mlo+Mlo')/2;
Shi=(Mhi+Mhi')/2;
end

function ub = symmetric_interval_lambda_upper(lo,hi)
ub=-inf;
for i=1:size(lo,1)
    radius=0;
    for j=1:size(lo,2)
        if i~=j
            radius=radius+max(abs([lo(i,j),hi(i,j)]));
        end
    end
    ub=max(ub,hi(i,i)+radius);
end
end

function ub = interval_spectral_norm_upper(lo,hi)
M=max(abs(lo),abs(hi));
ub=sqrt(norm(M,1)*norm(M,inf));
end

function verify_domain_bab(W1,b1,W2,A,P,J,epsilon,c,R,localR,minWidth)
% A box is discharged either by the global matrix inequality on the local
% square or by a direct natural interval extension of the decay margin.
stack=[-R,-R,R,R,0];
explored=0; localBoxes=0; directBoxes=0; unresolved=0; maxDepth=0;
worstDirect=-inf; minCertifiedUpper=inf;
tic;
while ~isempty(stack)
    box=stack(end,:); stack(end,:)=[]; explored=explored+1;
    lo=box(1:2)'; hi=box(3:4)'; depth=box(5); maxDepth=max(maxDepth,depth);
    if all(lo>=-localR) && all(hi<=localR)
        localBoxes=localBoxes+1; continue
    end
    [~,mhi]=direct_margin_interval(W1,b1,W2,A,P,J,epsilon,c,lo,hi);
    worstDirect=max(worstDirect,mhi);
    if mhi < -1e-10
        directBoxes=directBoxes+1; minCertifiedUpper=min(minCertifiedUpper,mhi); continue
    end
    widths=hi-lo;
    if max(widths)<=minWidth
        unresolved=unresolved+1;
        fprintf('UNRESOLVED lo=[%.9g %.9g] hi=[%.9g %.9g] mhi=%.9g\n',lo,hi,mhi);
        if unresolved>20, break; end
        continue
    end
    [~,k]=max(widths); mid=(lo(k)+hi(k))/2;
    hi1=hi; hi1(k)=mid; lo2=lo; lo2(k)=mid;
    stack=[stack;lo(1),lo(2),hi1(1),hi1(2),depth+1;lo2(1),lo2(2),hi(1),hi(2),depth+1]; %#ok<AGROW>
end
elapsed=toc;
fprintf('explored=%d local=%d direct=%d unresolved=%d maxDepth=%d minWidth=%.9g elapsed=%.3f s worstSeenUpper=%.9g bestCertifiedUpper=%.9g\n', ...
    explored,localBoxes,directBoxes,unresolved,maxDepth,minWidth,elapsed,worstDirect,minCertifiedUpper);
end

function [mlo,mhi] = direct_margin_interval(W1,b1,W2,A,P,J,epsilon,c,xlo,xhi)
[zlo,zhi]=linear_interval(W1,xlo,xhi,b1);
tlo=tanh(zlo); thi=tanh(zhi); [tlo,thi]=outward(tlo,thi);
[philo,phihi]=linear_interval(W2,tlo,thi,zeros(size(W2,1),1));
phi0=W2*tanh(b1);
glo=philo-phi0; ghi=phihi-phi0; [glo,ghi]=outward(glo,ghi);
dlo=zeros(size(zlo)); dhi=dlo;
for k=1:numel(zlo)
    vals=[sech(zlo(k))^2,sech(zhi(k))^2];
    dlo(k)=min(vals);
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
    vals=[alo*blo(k),alo*bhi(k),ahi*blo(k),ahi*bhi(k)];
    lo(k)=min(vals); hi(k)=max(vals);
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
inflate=1e-12*(1+max(abs(lo),abs(hi)));
lo=lo-inflate; hi=hi+inflate;
end
