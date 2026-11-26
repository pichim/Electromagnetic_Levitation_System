%%
clear; close all; clc;
set(groot, 'DefaultLineLineWidth', 1.5);

s = tf('s')

C = 1 / (s ) 

figure(1)

subplot(2,3,1)
bode(s+1)
title('s+1')

subplot(2,3,2)
bode(s-1)
title('s-1')

subplot(2,3,3)
bode(s)
title('s')

subplot(2,3,4)
bode(1/s)
title('1/s')

subplot(2,3,5)
bode(1/(s+1))
title('1/(s+1)')

subplot(2,3,6)
bode(1/(s-1))
title('1/(s-1)')

