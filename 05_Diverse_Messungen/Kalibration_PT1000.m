%%
clear; clc; close all;

U_mess = [2.36, 2.325, 2.29, 2.255, 2.215, 2.185, 2.134, 2.105, 2.058];
T_mess = [26.6, 40, 50, 60, 70, 80, 95, 105, 120];
p = polyfit(U_mess, T_mess, 1)

U_sim = linspace(2, 2.5, 100);
T_sim = polyval(p,U_sim);


%%

figure(1)
plot(U_mess, T_mess);
hold on
grid on
plot(U_sim, T_sim);
xlabel('Messspannung [V]')
ylabel('Temperatur [°C]')
legend('Messung', 'lineare Annäherung')
