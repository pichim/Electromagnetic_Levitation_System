%%
% 1: 7..11 s
%2:  

%%
close all; clc;
s = tf('s');

%Konstanten
a = 93.24;
b = -37.25;
g = 9.81;
k = 5.398;
I0 = 2;
x0 = 0.05;
m = 0.04;
Fg = m*g;
Tt = 0.1*10e-3; %Totzeit vom Sensor

% Berechnungen mit Formeln von Dokumentation 1999
c2 = 2/I0;
c1 = log(10)*(2*a*x0+b);
k_RS = c2/abs(c1);
T_RS = sqrt( Fg / (abs(c1)*g) );
G_RS = k_RS / (1 - s^2*T_RS^2) * exp(Tt);

C_PDT = k * (-6.556*s - 141) / (2.5e-5*s^2 + 0.01*s + 1);
C_PI = k * (0.0001*s+0.02) / (0.005*s);

C = C_PDT

L1 = C_PDT*G_RS;
T1 = L1 / (1+L1);
L2 = T1 * C_PI;
T2 = L2 / (1+L2);

figure(1)
bode(T1, T2)
grid on
legend('T1', 'T2')

%%
figure(2)
margin(L2)
grid on
legend('L1', 'L2')
