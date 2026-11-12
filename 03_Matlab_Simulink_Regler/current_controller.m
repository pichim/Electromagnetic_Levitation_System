clc, clear variables, close all;
%% Load and prepare data

Ts = 1 / 50e3; % Sampling time

% Load data
load 'Messungen'/Chirp_Spule_60s_05Offset.mat; % -> data (3 x 2840000)
% Messungen mit 0.5*Arbeitspunkt haben das beste Ergebnis geliefert
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
if isgraphics(4, 'figure')
    close(4);
end
if isgraphics(5, 'figure')
    close(5);
end

s = tf('s');
G = fselect(G, 0, 1e3); % Delete all frequencies above 1kHz 
Kp = 300;
Tn = 1 / (2*pi * 10);
Ki = Kp/Tn;
Ci = Kp + Ki / s;

L = G * Ci;
S = 1 / (1 + L);
T = 1 - S;

opts = bodeoptions;
opts.PhaseWrapping = 'on';          % Wrapping aktivieren
opts.PhaseWrappingBranch = -360;    % Phase wird in [-360°, 0°) gehalten


figure(4)
bode(L, 2*pi*G.Frequency, opts), grid on
legend('L', 'G');
title('Loop')


figure(5)
bode(T, S, 2*pi*G.Frequency, opts), grid on
title('Closed-Loop')
legend('T', 'S');

%% Frequenzkennlinienverfahren
if isgraphics(6, 'figure')
    close(6);
end
figure(6)
margin(L, opts), grid on
xlim([1e0 1e4])
legend('L');
title('Loop')


if isgraphics(7, 'figure')
    close(7);
end
figure(7)
bode(L,G, Ci, opts), grid on
xlim([1e0 1e4])
legend('L','G','Ci');
title('Loop')