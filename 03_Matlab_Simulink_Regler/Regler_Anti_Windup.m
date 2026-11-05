clc, clear variables
set(groot, 'defaultLineLineWidth', 1.5)
%%
% Konstanten von Dokumentation 2004
s = tf('s');
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

%% ControllerhohlHHhrjpohohl


% PID-T1
Kp = 4.5;
Ki = 0.03; % Can't be zero 
Kd = 0.109; 
Tf = 1/(2*pi*35);
LP = 1/(Tf*s + 1)^2;

C = (Kp + Ki/s + Kd*s) * LP;
L = G_RS * C;
T = L/(1+L);
S = 1/(1+L);

% Anti-Windup-Reset
% Ka = Ki / Kp;       % PI
Ka = sqrt(Ki / Kd); % PID-T1, Kd > 0
u_max = 10;
u_min = -u_max;

%% Plot
close all
figure(1)
bode(C, L, T)
grid on
legend('C', 'L', 'T')
set(findall(gcf, 'Type', 'line'), 'LineWidth', 2);

%%
figure(2)
pzmap(C, L, T)
grid on
legend('C', 'L', 'T')
lines = findall(gcf, 'Type', 'line');
set(lines, 'LineWidth', 1.5, 'MarkerSize', 8);


%%
r1 = 20
r2 = 40
r3 = 50
r4 = 

A1 = r1^2*pi

A2 = (r3^2-r2^2)

%% Regler Baumer sensor
% PID-T1
Kp = 3;
Ki = 0.05; % Can't be zero 
Kd = 0.05; 
Tf = 1/(2*pi*35);
LP = 1/(Tf*s + 1);

C = (Kp + Ki/s + Kd*s/(Tf*s+1)^2) * LP
L = G_RS * C;
T = L/(1+L);
S = 1/(1+L);
