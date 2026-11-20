%%
clear; close all; clc;
s = tf('s');

%%
G = -8.467 / (s^2 - 963.66);

T_lead = 1/31;%10 / (2*pi*20);
a = 0.3;

kp = 1;
Tn = 10;
ki = kp/Tn;
Tp = 1/500;


C_Lead = (T_lead*s + 1) / (a*T_lead*s+1);
C_Pi = kp + ki*s
C_T2 = 1 / (Tp + 1)^2

C = C_Lead * C_Pi * C_T2;

%%
figure(1)
bode(C)
grid on

%%
figure(2)
pzmap(G, C)

%%
figure(10)
bode(G, C*G)
legend('G', 'C*G')
grid on
title('Open Loop')
