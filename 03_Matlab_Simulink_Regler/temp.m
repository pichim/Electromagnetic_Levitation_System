clear;

Ts = 1 / 50e3; % Sampling time

% Load raw data (matrix of size 3 x 2840000)
load('Messungen/Chirp_NewSpule2_60s_8Offset.mat');

% Convert raw matrix into struct with time and values (N x 3)
data_raw = double(data);
clear data;

data.values = data_raw.';
data.time   = (0:size(data.values, 1)-1).' * Ts;

% Keep only the first half of samples
n_total  = size(data.values, 1);
half_end = floor(n_total / 2);

data.values = data.values(1:half_end, :);
data.time   = data.time(1:half_end, :);
N_half      = size(data.values, 1);

% Save processed struct to a new MAT file
save('Messungen/Chirp_NewSpule2_60s_8Offset_cut.mat', 'data');