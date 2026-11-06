set(cstprefs.tbxprefs, 'FrequencyUnits', 'Hz');
set(cstprefs.tbxprefs, 'UnwrapPhase', 'Off');
set(cstprefs.tbxprefs, 'Grid', 'On');

set(0, 'DefaultFigureToolbar', 'none')
% set(0, 'DefaultFigureToolbar', 'auto')

k = 1.2;
mon_pos = get(0,'MonitorPositions');
mon_pos = mon_pos(1, 3:4); % first monitor
fig_size_ini = [560, 420];
% fig_pos_ini  = [680, 458];
fig_pos_ini = mon_pos/2 - fig_size_ini/2; % /4 should be /2, like this better
fig_size = k * fig_size_ini;
fig_pos = fig_pos_ini - (k-1)/2 * fig_size_ini;
set(0, 'DefaultFigurePosition', round([fig_pos, fig_size]));

% set(0, 'DefaultAxesFontSize', 11);
% set(0, 'DefaultLegendFontSize', 11);

rel = version('-release');          % e.g., '2025a' or '2024a'
yr  = str2double(rel(1:4));
k = 1.0;
s = settings;
if yr >= 2025
    s.matlab.desktop.Zoom.PersonalValue = k * 100;
    % display("R2025a Display Settings");
else
    s.matlab.desktop.DisplayScaleFactor.PersonalValue = k;
    % display("R2024a Display Settings");
end

clc, clear variables

% lw = 1.0;
% set(0, 'defaultLineLineWidth', lw);
% set(0, ['Default', 'Stair', 'LineWidth'], lw);

% set(groot, 'defaultAxesColorOrder', mycolors);

beep off;

fprintf('   --- MATLAB preferences configured ---\n');

% %% startup configuration
% % function startup_(magnitudeUnits, frequencyUnits)
% 
%     % if ~strcmp(version('-release'), '2022a')
%     %     fprintf('   --- startup did not run ---\n');
%     %     return
%     % end
% 
%     if ~exist('magnitudeUnits', 'var') || isempty(magnitudeUnits)
%         magnitudeUnits = 'dB';
%         % magnitudeUnits = 'abs';
%     end
% 
%     if ~exist('frequencyUnits', 'var')|| isempty(frequencyUnits)
%         % frequencyUnits = 'rad/s';
%         frequencyUnits = 'Hz';
%     end
% 
%     linewidth = 1.2;
%     set(groot, 'DefaultLineLineWidth', linewidth);
% 
%     objectType = 'Stair';
%     propertyName = 'LineWidth';
%     set(groot, ['Default', objectType, propertyName], linewidth);
% 
%     set(groot, 'defaultAxesColorOrder', mycolors);
% 
%     set(groot, 'defaultAxesFontSize', 10);
%     set(groot, 'defaultLegendFontSize', 9);
%     % set(groot, 'defaulttextinterpreter','latex');  
%     % set(groot, 'defaultAxesTickLabelInterpreter','latex');  
%     % set(groot, 'defaultLegendInterpreter','latex'); 
% 
%     % set(groot, 'defaultfigurecolor', [30 30 30]/255);
%     % set(groot, 'defaultAxesXColor', [156 220 254]/255);
%     % set(groot, 'defaultAxesYColor', [156 220 254]/255);
%     % set(groot, 'defaultAxesZColor', [156 220 254]/255);
%     % set(groot, 'defaultAxesTitleColor', [156 220 254]/255);
%     % set(groot, {'DefaultAxesXColor', 'DefaultAxesYColor', 'DefaultAxesZColor'} , {'k','k','k'})
% 
%     cstPrefs = cstprefs.tbxprefs;
%     cstPrefs.FrequencyUnits = frequencyUnits;
%     cstPrefs.FrequencyScale = 'log';
%     cstPrefs.MagnitudeUnits = magnitudeUnits;
%     switch magnitudeUnits
%         case 'dB'
%             cstPrefs.MagnitudeScale = 'linear';
%         case 'abs'
%             cstPrefs.MagnitudeScale = 'log';
%         otherwise
%             % change nothing
%     end
%     cstPrefs.UnwrapPhase = 'off';
%     cstPrefs.Grid = 'on';
%     cstPrefs.TitleFontSize = 11;
%     cstPrefs.XYLabelsFontSize = 10;
%     cstPrefs.AxesForegroundColor = [0 0 0];
%     save(cstPrefs);
%     clear cstPrefs
% 
%     beep off;
% 
%     clc, clear all
%     fprintf('   --- welcome ---\n');;
% 
%     % datacursormode on
% 
% % end
