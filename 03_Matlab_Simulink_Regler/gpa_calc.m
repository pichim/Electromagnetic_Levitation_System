function [Gout,Gc,f] = gpa_calc(GPA_TD,Tsettle,fstart,fend,Wlen,wintyp,integ,shiftphase)
%GPA_CALC calculates the frd of a "struc with time" measurement
% [Gout,Gc,f] = gpa_calc(GPA_TD,Tsettle,fstart,fend,Wlen,wintyp,integ,shiftphase)
%
% input:
%   GPA_TD:     structure with time format: first col: input data / second col: output data
%   Tsettle:    [s] settling time before chirp, this data will be eliminated (default: 0s)
%   fstart:     [Hz] start frequency (default: 1/(t(end)+Ts))
%   fend:       [Hz] end frequency (default: 1/2/Ts)
%   Wlen:       windows length (default []: will split time data in sections for averaging)
%   wintyp:     windows type (default: hanning)
%   integ:      system with integrtor (default: 0)
%   shiftphase: [s] phase correction (default:0) porper system with ZOH: -Ts/2
% output:
%   Gout:       frd-object
%   Gc:         coherence (obtional)
%   f:          [Hz] frequency vector (obtional)

% Otto Fluder / ZHAW / IMS / fldr@zhaw.ch

if nargin<1 | isempty(GPA_TD)
    GPA_TD = evalin('base','G_td;');
end
if nargin<2 | isempty(Tsettle)
    Tsettle = 0;
end
if isstruct(GPA_TD) %structure with time
    t  = GPA_TD.time;
    xe = GPA_TD.signals.values(:,1);
    xa = GPA_TD.signals.values(:,2);
    if size(GPA_TD.signals.values,2)==3
        trig = GPA_TD.signals.values(:,3)==1;
        t  = GPA_TD.time(trig);
        xe = GPA_TD.signals.values(trig,1);
        xa = GPA_TD.signals.values(trig,2);
    end
elseif isnumeric(GPA_TD) %array
    t  = GPA_TD(:,1);
    xe = GPA_TD(:,2);
    xa = GPA_TD(:,3);
else %xpc
    t  = GPA_TD.TimeLog;
    xe = GPA_TD.OutputLog(:,1);
    xa = GPA_TD.OutputLog(:,2);
end
Ts = t(2)-t(1);
n0 = round(Tsettle/Ts) + 1;
xe = detrend(xe(n0:end-1),'constant');
xa = detrend(xa(n0:end-1),'constant');
if nargin<3 | isempty(fstart)
    fstart = 1/(t(end)+Ts);
end
if nargin<4 | isempty(fend)
    fend = 1/2/Ts;
end
if nargin<5 | isempty(Wlen)
    Wlen = [];
end
if nargin<6 | isempty(wintyp)
    wintyp = 'hann';
end
if nargin<7 | isempty(integ)
    integ = 0;
end
if nargin<8 | isempty(shiftphase)
    shiftphase = 0;
end
funits = 'Hz';
punits = '°';
aunits = 'dB';
flog = 1;
uw = 0;

if strcmp(funits,'Hz');
    fgain = 1;
else
    fgain = 2*pi;
end
if integ
    xa = filter([1 -1],Ts,xa);
end
if isempty(Wlen)
    NN = length(xe);
%    NN = floor(length(xe))/2;
    nover = ceil(NN/2);
%    [Gf,f] = tfestimate(xe,xa,rectwin(NN),nover,[],1/Ts);
    [Gf,f] = tfestimate(xe,xa,eval([wintyp,'(NN)']),nover,[],1/Ts);
    [Gc,f] = mscohere(xe,xa,eval([wintyp,'(NN)']),nover,[],1/Ts);
    NN = floor(NN/5);
    while NN >= 100
        nover = ceil(NN/2);
        [Gf2,f2] = tfestimate(xe,xa,eval([wintyp,'(NN)']),nover,[],1/Ts);
        [Gc2,f2] = mscohere(xe,xa,eval([wintyp,'(NN)']),nover,[],1/Ts);
        fcut = f2(25);
        i1 = find(f<fcut);
        i2 = find(f2>=fcut);
        Gf = [Gf(i1);Gf2(i2)];
        Gc = [Gc(i1);Gc2(i2)];
        f = [f(i1);f2(i2)];
        NN = floor(NN/5);
    end
else
    Wlen = min(Wlen,length(xe));
    nover = ceil(Wlen/2);
    [Gf,f] = tfestimate(xe,xa,eval([wintyp,'(Wlen)']),nover,[],1/Ts);
    [Gc,f] = mscohere(xe,xa,eval([wintyp,'(Wlen)']),nover,[],1/Ts);
end
if integ
    s = j*f*2*pi;
    Gf = Gf./s;
    Gf_a = abs(Gf);
    Gf_p = angle(Gf);
    Gf_p = Gf_p+(2*pi*f)*(Ts/2);
    Gf = Gf_a.*exp(Gf_p*j);
end
if shiftphase
    Gf_a = abs(Gf);
    Gf_p = angle(Gf);
    Gf_p = Gf_p+(2*pi*f)*(Ts/2);
    %Gf_p = Gf_p+(2*pi*f)*(Ts);
    Gf = Gf_a.*exp(Gf_p*j);
end
f = f*fgain;
i1 = find(f<=fstart,1,'last');
i2 = find(f>=fend,1,'first');
Nf = length(f);
if isempty(i1)
    i1 = 1;
end
if isempty(i2)
    i2 = length(f);
end
Gf = Gf(i1:i2);
Gc = Gc(i1:i2);
f  = f(i1:i2);
f(1) = fstart;
if i2<Nf
    f(end) = fend;
end
G = frd(Gf,f,'FrequencyUnit',funits);
%G = frd(Gf,f,Ts,'FrequencyUnit',funits);

if uw
    PhaseWrapping = 'off';
else
    PhaseWrapping = 'on';
end
if flog
    FreqScale = 'log';
else
    FreqScale = 'linear';
end
if strcmp(aunits,'dB')
    MagUnits = 'dB';
else
    MagUnits = 'abs';
end
if strcmp(punits,'°')
    PhaseUnits = 'deg';
else
    PhaseUnits = 'rad';
end
if nargout
    Gout = G;
else
    figure(gcf);
    hl = bodeplot(G);
    grid on
    if strcmp(MagUnits,'dB')
        MagScale = 'linear';
    else
        MagScale = 'log';
    end
    if strcmp(funits,'rad/s')
        xlim([fstart fend]*2*pi)
    else
        xlim([fstart fend])
    end
    setoptions(hl,'FreqScale',FreqScale,...
        'MagUnits',MagUnits,...
        'MagScale',MagScale,...
        'PhaseUnits',PhaseUnits,...
        'PhaseWrapping',PhaseWrapping);
    legend('show');
end
