function run_reproduction(mode)
% Reproduce calculations into generated/, preserving archived results/.
if nargin<1, mode='verify'; end
repo=fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(repo,'matlab'));
switch lower(string(mode))
    case "verify"
        revision_formal_verifier(fullfile(repo,'results','revision','revision_experiments.mat'), ...
            fullfile(repo,'generated','guarded_verification'));
    case "full"
        baseDir=fullfile(repo,'generated','base');
        revisionDir=fullfile(repo,'generated','revision');
        simulate_neural_lyapunov(baseDir);
        revision_training_study(fullfile(baseDir,'neural_lyapunov_results.mat'),revisionDir);
        revision_formal_verifier(fullfile(revisionDir,'revision_experiments.mat'), ...
            fullfile(repo,'generated','guarded_verification'));
    otherwise
        error('Use run_reproduction(''verify'') or run_reproduction(''full'').');
end
end
