clc, clear variables
set(groot, 'defaultLineLineWidth', 1.5)
s = tf('s');

%% System

close all; clc;
% Konstanten von Dokumentation 2004
a = 93.24
b = -37.25
g = 9.81
k = 5.398
I0 = 2
x0 = 0.05
m = 0.04
Fg = m*g
Tt = 0.1*10e-3 %Totzeit vom Sensor

% Berechnungen mit Formeln von Dokumentation
c2 = 2/I0
c1 = log(10)*(2*a*x0+b)
k_RS = c2/abs(c1)
T_RS = sqrt( Fg / (abs(c1)*g) )
G_RS = k_RS / (1 - s^2*T_RS^2) * exp(Tt)

%Reglerparameter
kp = 1
kd = -T_RS*kp

%C = kp + kd*s %PD Regler
T_Lead = 1;
alpha = 0.05;
Kk = 3;        % Schleifenverstärkung statisch (>1 nötig)
K = Kk / k_RS;
Td = 0.016;
Tf = Td/10;
Ti = 0.3;

C_Lead = (T_Lead*s+1) / (alpha*T_Lead*s+1); %Lead Regler
C_PD  = K * (1 + Td*s/(Tf*s+1));
C_PID = C_PD + K/(Ti*s);


LP = 1 % 1/(Tf*s+1)^1 % evtl. Tiefpass ergänzen

%Regelstrecke
L = G_RS * C_PD * LP
T = L/(1+L)
S = 1/(1+L)

figure(1)
bode(G_RS, T, C_PD, S)
xlim([1e-1 1e4])
grid on
legend('G_RS','T', 'C_PD', 'S')
%%
figure(2)
pzmap(T)
grid on
legend('G_RS','T')

%%
figure(3)
margin(L)
xlim([1e-2 1e3])
grid on
legend('L')


