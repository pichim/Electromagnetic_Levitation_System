%%
clc; close all; clear;

s = tf('s')

%%
G = -8.467 / (s^2 - 963.66)

Tn = 1 %Dort wo Integral aufhört
Tv = 1 % Dort wo Diff anfängt
kp = 1.413;

%ki = 0.1;
ki = kp/Tn

kd = 1.4159%0.0657;
%kd = Tv*kp


Tf  = 0.004869;  %1/(2*pi*35);
T3 = 0.00195;
Tt = 0.000474;
H = 1/(T3*s+1);%*exp(-Tt);


C_PID = (kp + kd * s + ki/s);
C_T2 = 1 / (T3*s+1) * 1 / (Tf*s+1);

C = C_PID * C_T2
L = C*G

T = L/(1+L)
S = 1/(1+L)

%%
close all;
figure(1)
bode(C, G, L)
xlim([1e-1 1e3])
grid on;
legend('C', 'G', 'closed loop')

figure(2)
bode(T,L)
xlim([1e-2 1e4])
grid on;
legend('T', 'L')

%%

figure(3)
margin(L)
grid on
