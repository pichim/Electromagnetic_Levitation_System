close all; clear; clc;
s = tf('s');

%%
close all
wp = 2*pi* 3;
wz = 2*pi* 30;
F = tf([1/wz 1], [1/wp 1]);

figure(99)
bode(F), grid on

%%
close all
load G_00.mat

Kp = 1.413;
Ki = 0.1;
Kd = 0.0657;
Tf  = 0.004869;  %1/(2*pi*35);
T3 = 0.00195;
Tt = 0.000474;
H = 1/(T3*s+1);%*exp(-Tt);
C = (Kp + Kd * s / (Tf*s + 1)^2 + H);

Tf2  = 1/(2*pi*400);
%C = C / (Tf*s + 1);

Ts_dsp = 1/500;
%G.Ts = Ts_dsp;

%C = c2d(C, Ts_dsp, 'tustin')

%%
T = 1/(2*pi*160)
a = 0.1

C_Lead = (T*s + 1) / (a*T*s + 1)
% Wäre noch ein versuch wert, den Regler auszuprobieren


figure(1)
subplot(1,2,1)
bode(G,C*G,C)
legend('G', 'C*G', 'C')
xlim([1e-2 1e3])
grid on

subplot(1,2,2)
margin(G)
xlim([1e-2 1e3])
legend('C*G')
grid on;

%%

z = tf('z', Ts_dsp);
% PDT2 * (1 + PI)

KK = (1 - z^-1) / Ts_dsp