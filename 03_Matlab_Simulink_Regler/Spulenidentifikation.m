%% Daten einlesen
close all; clear; clc;
load('Messungen/Chirp_NewSpule_60s_14Offset.mat');          % -> data (3 x 2840000)
fs = 50e3;                         
u  = double(data(1,:));           % Chirp-Spannung
y  = double(data(2,:));           % Antwort (Strom?)
en = data(3,:) > 0.5;             % Enable

% nur aktiven Bereich verwenden
i1 = find(en,1,'first');  i2 = find(en,1,'last');
t  = ((i1:i2)-i1)/fs;
u  = u(i1:i2);  y = y(i1:i2);

% Plot: jeden N-ten Punkt (Envelope bleibt grob erhalten)
N = 200;
figure(1); 
ax1 = subplot(2,1,1); plot(t(1:N:end), u(1:N:end)); ylabel('u / V'); grid on;
ax2 = subplot(2,1,2); plot(t(1:N:end), y(1:N:end)); ylabel('i / A'); xlabel('t / s');
grid on;
linkaxes([ax1 ax2],'x');


%% Frequenzgang schätzen
close all;
nfft = 2^16;
[H, f] = tfestimate(u - mean(u), y - mean(y), hann(nfft), nfft/2, nfft, fs);

figure(2)
subplot(2,1,1); 
semilogx(f, 20*log10(abs(H))); 
grid on; 
ylabel('|H| / dB');
xlim([1e-1 1e4])


subplot(2,1,2); 
semilogx(f, unwrap(angle(H))*180/pi); grid on;
ylabel('Phase / °'); xlabel('f / Hz'); xlim([1 fs/2]);
xlim([1e-1 1e4])
ylim([-250 180])

%% Frd Objekt erzeugen
close all;
idx = f<8e3;
GPA_TD = [u;y;t];
G = frd(H(idx),f(idx),'FrequencyUnit', 'Hz');
%G = gpa_calc(GPA_TD, i1, 0.05, 10e3); %läuft nicht

figure(3)
bode(G)
grid on;
ylim([-250 100])


%% Modell
if isgraphics(4, 'figure')
    close(4);
end
s = tf('s');
R = 3.3
L = 0.25
R_sim = 2.71
L_sim = 0.403
G_mod = 1 / (R + L*s)
G_sim = 1 / (R_sim + L_sim*s)

figure(4)
grid on
bode(G, G_mod, G_sim)
legend('Messung', 'Annäherung', 'Simulation')

%
sys = tfest(G, 1, 0);        % 1 Pol, 0 Nullstellen
[num, den] = tfdata(sys, 'v');   % G = num / (den(1)*s + den(2))
R = num / den(2)                % DC-Verstärkung = 1/R
L = den(1) * R                  % bei Normierung num/(L*s + R)
