/*
 * Implementation file for: Stromregler_RTBox
 * Generated with         : PLECS 5.0.6
 *                          PLECS RT Box 1 4.0.8
 * Generated on           : 29 Oct 2026 15:39:47
 */
#include "Stromregler_RTBox.h"
#ifndef PLECS_HEADER_Stromregler_RTBox_h_
#error The wrong header file "Stromregler_RTBox.h" was included. Please
#error check your include path to see whether this file name conflicts with
#error the name of another header file.
#endif /* PLECS_HEADER_Stromregler_RTBox_h_ */
#if defined(__GNUC__) && (__GNUC__ > 4)
#   define _ALIGNMENT 16
#   define _RESTRICT __restrict
#   define _ALIGN __attribute__((aligned(_ALIGNMENT)))
#   if defined(__clang__)
#      if __has_builtin(__builtin_assume_aligned)
#         define _ASSUME_ALIGNED(a) __builtin_assume_aligned(a, _ALIGNMENT)
#      else
#         define _ASSUME_ALIGNED(a) a
#      endif
#   else
#      define _ASSUME_ALIGNED(a) __builtin_assume_aligned(a, _ALIGNMENT)
#   endif
#else
#   ifndef _RESTRICT
#      define _RESTRICT
#   endif
#   ifndef _ALIGN
#      define _ALIGN
#   endif
#   ifndef _ASSUME_ALIGNED
#      define _ASSUME_ALIGNED(a) a
#   endif
#endif
#include <stdint.h>
#include <stdbool.h>
#include <math.h>
#include <string.h>
#include "plexim/AnalogIn.h"
#include "plexim/DigitalIn.h"
#include "plexim/DigitalOut.h"
#include "plexim/hw_wrapper.h"
#include "plexim/AnalogOut.h"
#include "plexim/SFP.h"
#include "plexim/HIL_Framework.h"
#include "plexim/DigitalOverride.h"
#include "plexim/DataCapture.h"
#include "plexim/ProgrammableValue.h"
#include "plexim/ToFile.h"
#define PLECSRunTimeError(msg) Stromregler_RTBox_errorStatus = msg
#define Stromregler_RTBox_UNCONNECTED 0
static double Stromregler_RTBox_deriv[2] _ALIGN;
static uint32_t Stromregler_RTBox_tickLo;
static int32_t Stromregler_RTBox_tickHi;
/* Block outputs */
static double Stromregler_RTBox_B_I_Soll_Begrenzung; /* Stromregler_RTBox/I_Soll_Begrenzung */
static double Stromregler_RTBox_B_UZK_Nenner; /* Stromregler_RTBox/UZK_Nenner */
static double Stromregler_RTBox_B_Saturation; /* Stromregler_RTBox/Continuous PID Controller3/Saturation/internal/Saturation Select/constant/Saturation */
static double Stromregler_RTBox_B_Min_Max; /* Stromregler_RTBox/Continuous PID Controller3/Anti-windup method/Conditional Integration/Dead Zone4/Min/Max */
static double Stromregler_RTBox_B_Min_Max1; /* Stromregler_RTBox/Continuous PID Controller3/Anti-windup method/Conditional Integration/Dead Zone4/Min/Max1 */
static bool Stromregler_RTBox_B_RelationalOperator; /* Stromregler_RTBox/Continuous PID Controller3/Anti-windup method/Conditional Integration/Relational Operator */
static double Stromregler_RTBox_B_Saturation_1[4]; /* Stromregler_RTBox/Saturation */
static double Stromregler_RTBox_B_UZKJL2_8; /* Stromregler_RTBox/UZK JL2_8 */
static double Stromregler_RTBox_B_ICDJL2_14; /* Stromregler_RTBox/ICD  JL2_14 */
static bool Stromregler_RTBox_B_DigitalIn4; /* Stromregler_RTBox/Digital In4 */
static double Stromregler_RTBox_B_U_Simulink; /* Stromregler_RTBox/U_Simulink */
static double Stromregler_RTBox_B_Spannung_OK; /* Stromregler_RTBox/Spannung_OK */
static bool Stromregler_RTBox_B_Freigabe; /* Stromregler_RTBox/Freigabe */
static bool Stromregler_RTBox_B_Reset_PI; /* Stromregler_RTBox/Reset_PI */
static double Stromregler_RTBox_B_Integrator1; /* Stromregler_RTBox/Continuous PID Controller3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1 */
static double Stromregler_RTBox_B_Sum; /* Stromregler_RTBox/Sum */
static double Stromregler_RTBox_B_Subtract2; /* Stromregler_RTBox/Subtract2 */
static double Stromregler_RTBox_B_Sum_1; /* Stromregler_RTBox/Continuous PID Controller3/Continous Time/Sum */
static double Stromregler_RTBox_B_Product3; /* Stromregler_RTBox/Product3 */
static double Stromregler_RTBox_B_Sum_2; /* Stromregler_RTBox/Continuous PID Controller3/Anti-windup method/Conditional Integration/Sum */
static double Stromregler_RTBox_B_Sum1; /* Stromregler_RTBox/Continuous PID Controller3/Anti-windup method/Conditional Integration/Sum1 */

/* Model states */
static bool Stromregler_RTBox_X_Spannung_OK; /* Stromregler_RTBox/Spannung_OK */
static double Stromregler_RTBox_X_Integrator1_x; /* Stromregler_RTBox/Continuous PID Controller3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1 */
static bool Stromregler_RTBox_X_Integrator1_i1_first; /* Stromregler_RTBox/Continuous PID Controller3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1 */
static double Stromregler_RTBox_X_I_Filter_fg_500_; /* Stromregler_RTBox/I_Filter(fg=500) */

#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
static double Stromregler_RTBox_ExtModeBuffer[2];
const double * const Stromregler_RTBox_ExtModeSignals[] = {
   &Stromregler_RTBox_B_ICDJL2_14,
   &Stromregler_RTBox_B_Sum,
   &Stromregler_RTBox_B_Spannung_OK,
   &Stromregler_RTBox_B_Saturation,
   &Stromregler_RTBox_ExtModeBuffer[0],
   &Stromregler_RTBox_ExtModeBuffer[1],
   &Stromregler_RTBox_B_Product3,
   &Stromregler_RTBox_B_U_Simulink,
   &Stromregler_RTBox_B_Saturation,
   &Stromregler_RTBox_B_Product3,
   &Stromregler_RTBox_B_Product3,
   &Stromregler_RTBox_B_Product3,
   &Stromregler_RTBox_B_Product3,
   &Stromregler_RTBox_B_I_Soll_Begrenzung,
   &Stromregler_RTBox_B_Sum,
   &Stromregler_RTBox_B_Subtract2,
   &Stromregler_RTBox_B_Saturation,
   &Stromregler_RTBox_B_Sum,
   &Stromregler_RTBox_B_UZKJL2_8,
   &Stromregler_RTBox_B_Sum
};
#endif /* defined(EXTERNAL_MODE) */
Stromregler_RTBox_Parameters Stromregler_RTBox_P = {
   /* Parameter 'K' of
    *  Gain : 'Stromregler_RTBox/K_U_I'
    */
   -0.800000000000000044
};
const char * Stromregler_RTBox_errorStatus;
const double Stromregler_RTBox_sampleTime = 2.00000000000000016e-05;
const char * const Stromregler_RTBox_checksum =
   "005c548cc0684c6ad5c0dced902b833158e5fc54";
/* Target declarations */
struct PlxDataCaptureRegistry plxDataCaptureRegistry[1];
const int plxUseEthercat = 0;
struct PlxProgrammableValueRegistry plxProgrammableValueRegistry[1];
struct PlxToFileRegistry plxToFileRegistry[1];
const char* plxAssertionMessages[] = {
   "","","","","","","","","","","","","","","","","","","","","","","","","",
   "","","","","","","",
};
void Stromregler_RTBox_initialize(double time)
{
   double remainder;
   Stromregler_RTBox_errorStatus = NULL;
   Stromregler_RTBox_tickHi =
      floor(time/(4294967296.0*Stromregler_RTBox_sampleTime));
   remainder = time - Stromregler_RTBox_tickHi*4294967296.0*
               Stromregler_RTBox_sampleTime;
   Stromregler_RTBox_tickLo = floor(
                                    remainder/Stromregler_RTBox_sampleTime +
                                    .5);
   remainder -= Stromregler_RTBox_tickLo*Stromregler_RTBox_sampleTime;
   if (fabs(remainder) > 1e-6*fabs(time))
   {
      Stromregler_RTBox_errorStatus =
         "Start time must be an integer multiple of the base sample time.";
   }

   /* Target pre-initialization */
   plxSetAnalogInputVoltage(0);
   plxSetupDACs(0);
   plxSetDigitalOutVoltage(0);
   plxInitDigitalOut();
   initPWMCapture();
   plxInitDigitalOverride();
   plxSetupAnalogSampling(0, 1333, 2.00000000000000016e-05);
   plxSetMaxNumConsecutiveOverruns(5);
   plxSetupSFPSyncMaster(0, 0, 0, 0);
   plxSetupSFPSyncSlave(0, 0, 0);


   /* Initialization for Analog In : 'Stromregler_RTBox/UZK JL2_8' */
   setupAnalogIn(3, 2.100000000e+01f, 0.000000000e+00f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Analog In : 'Stromregler_RTBox/ICD  JL2_14' */
   setupAnalogIn(5, 7.142857143e+00f, -1.071428571e+01f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Digital In : 'Stromregler_RTBox/Digital In4' */
   plxSetupDigitalInput(26, 3);

   /* Initialization for Analog In : 'Stromregler_RTBox/U_Simulink' */
   setupAnalogIn(0, 1.000000000e+00f, 0.000000000e+00f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Relay : 'Stromregler_RTBox/Spannung_OK' */
   Stromregler_RTBox_X_Spannung_OK = 0;

   /* Initialization for Integrator : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1' */
   Stromregler_RTBox_X_Integrator1_x = 0;
   Stromregler_RTBox_X_Integrator1_i1_first = 1;

   /* Initialization for Transfer Function : 'Stromregler_RTBox/I_Filter(fg=500)' */
   Stromregler_RTBox_X_I_Filter_fg_500_ = 0.;

   /* Initialization for Analog In : 'Stromregler_RTBox/IAB JL2_16' */
   setupAnalogIn(4, 7.142857143e+00f, -1.071428571e+01f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Digital Out : 'Stromregler_RTBox/Enable1' */
   setupDigitalOut(12, DO_GPIO, DO_NINV);
   setupDigitalOut(13, DO_GPIO, DO_NINV);
   setupDigitalOut(14, DO_GPIO, DO_NINV);

   /* Initialization for PWM Out : 'Stromregler_RTBox/S J2' */
   setPWMOutPrd(16, 1333);
   setPWMOutPrd(17, 1333);
   setPWMOutPrd(18, 1333);
   setPWMOutPrd(19, 1333);
   setPWMOutShft(16, 0);
   setPWMOutShft(17, 0);
   setPWMOutShft(18, 0);
   setPWMOutShft(19, 0);
   setupDigitalOut(16, DO_PWM, DO_NINV);
   setupPWMGen(16, 1, 0, 0, 0, 16, 1, 0, 1, 0);
   plxSetPWMSafeState(16, 0);
   plxSetPWMProtectionUnit(16, PLX_PSP_UNIT1);
   setupDigitalOut(17, DO_PWM, DO_NINV);
   setupPWMGen(17, 1, 0, 0, 0, 17, 1, 1, 1, 0);
   plxSetPWMSafeState(17, 0);
   plxSetPWMProtectionUnit(17, PLX_PSP_UNIT1);
   setupDigitalOut(18, DO_PWM, DO_NINV);
   setupPWMGen(18, 1, 0, 0, 0, 18, 1, 0, 1, 0);
   plxSetPWMSafeState(18, 0);
   plxSetPWMProtectionUnit(18, PLX_PSP_UNIT1);
   setupDigitalOut(19, DO_PWM, DO_NINV);
   setupPWMGen(19, 1, 0, 0, 0, 19, 1, 1, 1, 0);
   plxSetPWMSafeState(19, 0);
   plxSetPWMProtectionUnit(19, PLX_PSP_UNIT1);
}

void Stromregler_RTBox_step(void)
{
   if (Stromregler_RTBox_errorStatus)
   {
      return;
   }

   /* Analog In : 'Stromregler_RTBox/UZK JL2_8' */
   Stromregler_RTBox_B_UZKJL2_8 = getAnalogIn(3);

   /* Analog In : 'Stromregler_RTBox/ICD  JL2_14' */
   Stromregler_RTBox_B_ICDJL2_14 = getAnalogIn(5);

   /* Digital In : 'Stromregler_RTBox/Digital In4' */
   Stromregler_RTBox_B_DigitalIn4 = getDigitalIn(26);

   /* Analog In : 'Stromregler_RTBox/U_Simulink' */
   Stromregler_RTBox_B_U_Simulink = getAnalogIn(0);

   /* Saturation : 'Stromregler_RTBox/I_Soll_Begrenzung'
    * incorporates
    *  Gain : 'Stromregler_RTBox/K_U_I'
    */
   Stromregler_RTBox_B_I_Soll_Begrenzung = Stromregler_RTBox_P.K_U_I_K*
                                           Stromregler_RTBox_B_U_Simulink;
   if (Stromregler_RTBox_B_I_Soll_Begrenzung > 3.69229999999999992)
   {
      Stromregler_RTBox_B_I_Soll_Begrenzung = 3.69229999999999992;
   }
   else if (Stromregler_RTBox_B_I_Soll_Begrenzung < 0.)
   {
      Stromregler_RTBox_B_I_Soll_Begrenzung = 0.;
   }

   /* Saturation : 'Stromregler_RTBox/UZK_Nenner' */
   Stromregler_RTBox_B_UZK_Nenner = Stromregler_RTBox_B_UZKJL2_8;
   if (Stromregler_RTBox_B_UZK_Nenner < 1.)
   {
      Stromregler_RTBox_B_UZK_Nenner = 1.;
   }

   /* Relay : 'Stromregler_RTBox/Spannung_OK' */
   {
      double u = Stromregler_RTBox_B_UZKJL2_8;
      if (Stromregler_RTBox_X_Spannung_OK && u < 17.)
      {
         Stromregler_RTBox_X_Spannung_OK = 0;
      }
      else if (!Stromregler_RTBox_X_Spannung_OK && u > 18.)
      {
         Stromregler_RTBox_X_Spannung_OK = 1;
      }
   }
   Stromregler_RTBox_B_Spannung_OK =
      (Stromregler_RTBox_X_Spannung_OK) ? 1. : 0.;

   /* Logical Operator : 'Stromregler_RTBox/Freigabe' */
   Stromregler_RTBox_B_Freigabe = Stromregler_RTBox_B_DigitalIn4 &&
                                  Stromregler_RTBox_B_Spannung_OK;

   /* Logical Operator : 'Stromregler_RTBox/Reset_PI' */
   Stromregler_RTBox_B_Reset_PI = !Stromregler_RTBox_B_Freigabe;

   /* Integrator : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1' */
   if (Stromregler_RTBox_X_Integrator1_i1_first ||
       (Stromregler_RTBox_B_Reset_PI != 0))
   {
      Stromregler_RTBox_X_Integrator1_x = 0.;
   }
   Stromregler_RTBox_B_Integrator1 = Stromregler_RTBox_X_Integrator1_x;

   /* Sum : 'Stromregler_RTBox/Sum'
    * incorporates
    *  Transfer Function : 'Stromregler_RTBox/I_Filter(fg=500)'
    *  Constant : 'Stromregler_RTBox/I_Offset'
    */
   Stromregler_RTBox_B_Sum =
      (3124.99999999999955*
       Stromregler_RTBox_X_I_Filter_fg_500_) - (-0.00600000000000000012);

   /* Sum : 'Stromregler_RTBox/Subtract2' */
   Stromregler_RTBox_B_Subtract2 = Stromregler_RTBox_B_I_Soll_Begrenzung -
                                   Stromregler_RTBox_B_Sum;

   /* Sum : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Sum'
    * incorporates
    *  Product : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Product'
    *  Constant : 'Stromregler_RTBox/Continuous PID\nController3/Source Select/internal/Constant'
    *  Product : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Product3'
    *  Sum : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Sum1'
    *  Product : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Product2'
    *  Constant : 'Stromregler_RTBox/Continuous PID\nController3/Source Select/internal/Constant2'
    *  Constant : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Kd Integrator/Kd = 0/Constant'
    *  Constant : 'Stromregler_RTBox/Continuous PID\nController3/Source Select/internal/Constant3'
    */
   Stromregler_RTBox_B_Sum_1 =
      (Stromregler_RTBox_B_Subtract2 *
       101.700000000000003) +
      (((Stromregler_RTBox_B_Subtract2 *
         0.) - 0.) * 0.) + Stromregler_RTBox_B_Integrator1;

   /* Saturation : 'Stromregler_RTBox/Continuous PID\nController3/Saturation/internal/Saturation Select/constant/Saturation' */
   Stromregler_RTBox_B_Saturation = Stromregler_RTBox_B_Sum_1;
   if (Stromregler_RTBox_B_Saturation > 24.)
   {
      Stromregler_RTBox_B_Saturation = 24.;
   }
   else if (Stromregler_RTBox_B_Saturation < -24.)
   {
      Stromregler_RTBox_B_Saturation = -24.;
   }

   /* Product : 'Stromregler_RTBox/Product3' */
   Stromregler_RTBox_B_Product3 = 1. / Stromregler_RTBox_B_UZK_Nenner *
                                  Stromregler_RTBox_B_Saturation;

   /* Relational Operator : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Relational\nOperator'
    * incorporates
    *  Product : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Product'
    *  Constant : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Constant1'
    */
   Stromregler_RTBox_B_RelationalOperator =
      (Stromregler_RTBox_B_Sum_1 * Stromregler_RTBox_B_Subtract2) > 0.;

   /* Sum : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Sum' */
   Stromregler_RTBox_B_Sum_2 = -Stromregler_RTBox_B_Sum_1 +
                               Stromregler_RTBox_B_Saturation;

   /* Sum : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Sum1'
    * incorporates
    *  Gain : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/rtol'
    *  Abs : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Abs4'
    *  Constant : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/atol'
    */
   Stromregler_RTBox_B_Sum1 =
      (9.99999999999999955e-07*
       fabs(Stromregler_RTBox_B_Sum_1)) + 2.22044604925031308e-14;

   /* Minimum / Maximum : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Dead Zone4/Min\/Max'
    * incorporates
    *  Zero-Order Hold : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Dead Zone4/Zero-Order\nHold1'
    */
   {
      double u, y;
      y = Stromregler_RTBox_B_Sum_2;
      u = Stromregler_RTBox_B_Sum1;
      if (u < y)
         y = u;
      Stromregler_RTBox_B_Min_Max = y;
   }

   /* Minimum / Maximum : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Dead Zone4/Min\/Max1'
    * incorporates
    *  Gain : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Dead Zone4/Gain'
    */
   {
      double u, y;
      y = Stromregler_RTBox_B_Min_Max;
      u = -1.*Stromregler_RTBox_B_Sum1;
      if (u > y)
         y = u;
      Stromregler_RTBox_B_Min_Max1 = y;
   }
   /* Digital Out : 'Stromregler_RTBox/Enable1' */
   writeDigitalOut(12, Stromregler_RTBox_B_Freigabe);
   writeDigitalOut(13, ((bool)0.));
   writeDigitalOut(14, Stromregler_RTBox_B_Freigabe);
   /* Saturation : 'Stromregler_RTBox/Saturation' */
   Stromregler_RTBox_B_Saturation_1[0] = Stromregler_RTBox_B_Product3;
   if (Stromregler_RTBox_B_Saturation_1[0] > 0.900000000000000022)
   {
      Stromregler_RTBox_B_Saturation_1[0] = 0.900000000000000022;
   }
   else if (Stromregler_RTBox_B_Saturation_1[0] < -0.900000000000000022)
   {
      Stromregler_RTBox_B_Saturation_1[0] = -0.900000000000000022;
   }
   Stromregler_RTBox_B_Saturation_1[1] = Stromregler_RTBox_B_Product3;
   if (Stromregler_RTBox_B_Saturation_1[1] > 0.900000000000000022)
   {
      Stromregler_RTBox_B_Saturation_1[1] = 0.900000000000000022;
   }
   else if (Stromregler_RTBox_B_Saturation_1[1] < -0.900000000000000022)
   {
      Stromregler_RTBox_B_Saturation_1[1] = -0.900000000000000022;
   }
   Stromregler_RTBox_B_Saturation_1[2] = Stromregler_RTBox_B_Product3;
   if (Stromregler_RTBox_B_Saturation_1[2] > 0.900000000000000022)
   {
      Stromregler_RTBox_B_Saturation_1[2] = 0.900000000000000022;
   }
   else if (Stromregler_RTBox_B_Saturation_1[2] < -0.900000000000000022)
   {
      Stromregler_RTBox_B_Saturation_1[2] = -0.900000000000000022;
   }
   Stromregler_RTBox_B_Saturation_1[3] = Stromregler_RTBox_B_Product3;
   if (Stromregler_RTBox_B_Saturation_1[3] > 0.900000000000000022)
   {
      Stromregler_RTBox_B_Saturation_1[3] = 0.900000000000000022;
   }
   else if (Stromregler_RTBox_B_Saturation_1[3] < -0.900000000000000022)
   {
      Stromregler_RTBox_B_Saturation_1[3] = -0.900000000000000022;
   }

   /* PWM Out : 'Stromregler_RTBox/S J2' */
   {
      const int periodPWM_int = 1334;
      const float gain = 6.667500000e+02f;
      {
         int cmpPWM =
            (int)(((Stromregler_RTBox_B_Saturation_1[0]) +
                   1.000000000e+00f)*gain + 0.5);
         if (cmpPWM < 0)
         {
            cmpPWM = 0;
         }
         else if (cmpPWM > periodPWM_int)
         {
            cmpPWM = periodPWM_int;
         }
         setPWMOutCmp(16, cmpPWM);
      }
      {
         int cmpPWM =
            (int)(((Stromregler_RTBox_B_Saturation_1[1]) +
                   1.000000000e+00f)*gain + 0.5);
         if (cmpPWM < 0)
         {
            cmpPWM = 0;
         }
         else if (cmpPWM > periodPWM_int)
         {
            cmpPWM = periodPWM_int;
         }
         setPWMOutCmp(17, cmpPWM);
      }
      {
         int cmpPWM =
            (int)(((Stromregler_RTBox_B_Saturation_1[2]) +
                   1.000000000e+00f)*gain + 0.5);
         if (cmpPWM < 0)
         {
            cmpPWM = 0;
         }
         else if (cmpPWM > periodPWM_int)
         {
            cmpPWM = periodPWM_int;
         }
         setPWMOutCmp(18, cmpPWM);
      }
      {
         int cmpPWM =
            (int)(((Stromregler_RTBox_B_Saturation_1[3]) +
                   1.000000000e+00f)*gain + 0.5);
         if (cmpPWM < 0)
         {
            cmpPWM = 0;
         }
         else if (cmpPWM > periodPWM_int)
         {
            cmpPWM = periodPWM_int;
         }
         setPWMOutCmp(19, cmpPWM);
      }
   }

#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
   Stromregler_RTBox_ExtModeBuffer[0] = (double)Stromregler_RTBox_B_Freigabe;
   Stromregler_RTBox_ExtModeBuffer[1] =
      (double)Stromregler_RTBox_B_DigitalIn4;
#endif /* defined(EXTERNAL_MODE) */

   if (Stromregler_RTBox_errorStatus)
   {
      return;
   }

   /* Update for Integrator : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1' */
   Stromregler_RTBox_X_Integrator1_i1_first = 0;

   /* Derivatives for Integrator : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1'
    * incorporates
    *  Sum : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Sum3'
    *  Product : 'Stromregler_RTBox/Continuous PID\nController3/Continous Time/Product1'
    *  Constant : 'Stromregler_RTBox/Continuous PID\nController3/Source Select/internal/Constant1'
    *  Logical Operator : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Logical\nOperator2'
    *  Logical Operator : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Logical\nOperator1'
    *  Sum : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Dead Zone4/Sum2'
    *  Constant : 'Stromregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Constant'
    */
   if (Stromregler_RTBox_B_Reset_PI != 0)
   {
      Stromregler_RTBox_deriv[0] = 0;
   }
   else
   {
      Stromregler_RTBox_deriv[0] =
         (Stromregler_RTBox_B_Subtract2 * 816.799999999999955 *
          ((double)(!(Stromregler_RTBox_B_RelationalOperator &&
                      (-Stromregler_RTBox_B_Min_Max1 +
                    Stromregler_RTBox_B_Sum_2))))) + 0.;
   }

   /* Derivatives for Transfer Function : 'Stromregler_RTBox/I_Filter(fg=500)'
    * incorporates
    *  Analog In : 'Stromregler_RTBox/IAB JL2_16'
    */
   Stromregler_RTBox_deriv[1] = (getAnalogIn(4))-3124.99999999999955*
                                Stromregler_RTBox_X_I_Filter_fg_500_;

   /* Update continuous states */
   Stromregler_RTBox_X_Integrator1_x += 2.00000000000000016e-05*
                                        Stromregler_RTBox_deriv[0];
   Stromregler_RTBox_X_I_Filter_fg_500_ += 2.00000000000000016e-05*
                                           Stromregler_RTBox_deriv[1];
}

void Stromregler_RTBox_terminate(void)
{
}
