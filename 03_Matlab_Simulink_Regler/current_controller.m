clc, clear variables
%% Load and prepare data

Ts = 1 / 50e3; % Sampling time

% Load data
load 'Chirp_Spule_20kHz.mat'; % -> data (3 x 2840000)
data_raw = data;
clear data
data.values = double(data_raw).'
data.time = (0:length(data.values)-1).' * Ts;

idx.inp = 1;     % What signal, what unit?
idx.out = 2;
idx.enable  = 3;

% Cut data
idx_cut = data.values(:, idx.enable) > 0.5;
data.values = data.values(idx_cut, :);
data.time   = data.time(idx_cut, :);
data.time = data.time - data.time(1);
N = length(data.values)

figure(1)
subplot(311)
plot(data.time, data.values(:, idx.inp)), grid on
subplot(312)
plot(data.time, data.values(:, idx.out)), grid on
subplot(313)
plot(data.time, data.values(:, idx.enable)), grid on


%% Frequency Response Estimate

Nest     = floor(N / 50);
koverlap = 0.5;
Noverlap = round(koverlap * Nest);
window   = hann(Nest);
[g, f] = tfestimate(data.values(:, idx.inp), ...
    data.values(:, idx.out), ...
    window, Noverlap, Nest, 1/Ts);
c = mscohere(data.values(:, idx.inp), ...
    data.values(:, idx.out), ...
    window, Noverlap, Nest, 1/Ts);

% Create frd-objects
% G = frd(g, f, Ts, 'Units', 'Hz'); % Time discrete
% C = frd(c, f, Ts, 'Units', 'Hz');
G = frd(g, f, 'Units', 'Hz'); % Time continous
C = frd(c, f, 'Units', 'Hz');

figure(2)
bode(G, 2*pi*G.Frequency), grid on
title('Plant')

opt = bodeoptions('cstprefs');
opt.MagUnits = 'abs';
opt.MagScale = 'linear';

figure(3)
bodemag(C, 2*pi*C.Frequency, opt), grid on
title('Coherence')


%% Current Controller

s = tf('s');

Kp = 700;
Tn = 1 / (2*pi * 30);
Ki = Kp/Tn;
Ci = Kp + Ki / s;

L = G * Ci;
S = 1 / (1 + L);
T = 1 - S;

figure(4)
bode(L, 2*pi*G.Frequency), grid on
title('Loop')

figure(5)
bode(T, S, 2*pi*G.Frequency), grid on
title('Closed-Loop')
