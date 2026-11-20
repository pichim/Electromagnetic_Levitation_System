%%
clear; close all; clc;
s = tf('s');

%%
L_Spule = 0.25; %H
R_Spule = 3.3; %Ohm
Tt = 1e-3;
G_Spule = 1 / (L_Spule*s + R_Spule);
G_Kugel = -8.467 / (s^2 - 963.66);
C_Spule = (100*s + 1.257e5)/s;
G = G_Kugel + G_Spule;% * exp(-Tt*s);

T_lead = 10 / (2*pi*20);
a = 0.3;

kp = 1;
Tn = 10;
ki = kp/Tn;
Tp = 1/500;
k0 = db2mag(10);


C_Lead = (T_lead*s + 1) / (a*T_lead*s+1);
C_Pi = kp + ki*s;
C_T2 = 1 / (Tp*s + 1)^2;

C = k0 * C_Lead% * C_T2;%* C_Pi * C_T2;
L = C*G;
T = L/(1+L);
%controlSystemDesigner('rlocus',G,C)
[num, den] = tfdata(C, 'v')
%%
opts = bodeoptions;
opts.PhaseWrapping = 'on';          % Wrapping aktivieren
opts.PhaseWrappingBranch = -360;    % Phase wird in [-360°, 0°) gehalten

figure(1)
bode(C)
grid on

%%
figure(2)
pzmap(G, C)
legend('G', 'C')
grid on

%%
figure(10)
bode(G, L, T, opts)
legend('G', 'L', 'T')
grid on
title('Open Loop')
