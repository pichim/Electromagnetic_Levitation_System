/*
 * Implementation file for: Chirp_Messung_Spule
 * Generated with         : PLECS 5.0.6
 *                          PLECS RT Box 1 4.0.8
 * Generated on           : 5 Nov 2026 16:04:50
 */
#include "Chirp_Messung_Spule.h"
#ifndef PLECS_HEADER_Chirp_Messung_Spule_h_
#error The wrong header file "Chirp_Messung_Spule.h" was included. Please
#error check your include path to see whether this file name conflicts with
#error the name of another header file.
#endif /* PLECS_HEADER_Chirp_Messung_Spule_h_ */
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
#include "plexim/ToFile.h"
#include "plexim/hw_wrapper.h"
#include "plexim/AnalogOut.h"
#include "plexim/SFP.h"
#include "plexim/HIL_Framework.h"
#include "plexim/DigitalOverride.h"
#include "plexim/DataCapture.h"
#include "plexim/ProgrammableValue.h"
#define PLECSRunTimeError(msg) Chirp_Messung_Spule_errorStatus = msg
static double plecsmod(double a, double b)
{
   if (!b)
   {
      return a;
   }
   else
   {
      double r = fmod(a, b);
      if ((r < 0 && b > 0) || (r > 0 && b < 0))
      {
         r += b;
      }
      return r;
   }
}
#define Chirp_Messung_Spule_UNCONNECTED 0
static uint32_t Chirp_Messung_Spule_D_uint32_t[1];
static double Chirp_Messung_Spule_deriv[1] _ALIGN;
static uint32_t Chirp_Messung_Spule_tickLo;
static int32_t Chirp_Messung_Spule_tickHi;
/* Block outputs */
static double Chirp_Messung_Spule_B_UZK_Nenner; /* Chirp_Messung_Spule/UZK_Nenner */
static bool Chirp_Messung_Spule_B_Monoflop; /* Chirp_Messung_Spule/Chirp/Monoflop */
static double Chirp_Messung_Spule_B_ManualSwitch1; /* Chirp_Messung_Spule/Manual Switch1 */
static double Chirp_Messung_Spule_B_Sub; /* Chirp_Messung_Spule/Chirp/Sub */
static double Chirp_Messung_Spule_B_Saturation[4]; /* Chirp_Messung_Spule/Saturation */
static double Chirp_Messung_Spule_B_UZKJL2_8; /* Chirp_Messung_Spule/UZK JL2_8 */
static double Chirp_Messung_Spule_B_IABJL2_16; /* Chirp_Messung_Spule/IAB JL2_16 */
static double Chirp_Messung_Spule_B_ICDJL2_14; /* Chirp_Messung_Spule/ICD  JL2_14 */
static bool Chirp_Messung_Spule_B_DigitalIn4; /* Chirp_Messung_Spule/Digital In4 */
static double Chirp_Messung_Spule_B_Spannung_OK; /* Chirp_Messung_Spule/Spannung_OK */
static bool Chirp_Messung_Spule_B_Freigabe; /* Chirp_Messung_Spule/Freigabe */
static double Chirp_Messung_Spule_B_Sum; /* Chirp_Messung_Spule/Sum */
static double Chirp_Messung_Spule_B_Delay; /* Chirp_Messung_Spule/Chirp/Sub/Delay */
static double Chirp_Messung_Spule_B_Sum7; /* Chirp_Messung_Spule/Chirp/Sub/Sum7 */
static double Chirp_Messung_Spule_B_In1; /* Chirp_Messung_Spule/Chirp/Sub/In1 */
static double Chirp_Messung_Spule_B_Switch; /* Chirp_Messung_Spule/Chirp/Sub/Switch */
static bool Chirp_Messung_Spule_B_LogicalOperator; /* Chirp_Messung_Spule/Chirp/Logical Operator */
static double Chirp_Messung_Spule_B_Gain1; /* Chirp_Messung_Spule/Gain1 */
static double Chirp_Messung_Spule_B_Product3; /* Chirp_Messung_Spule/Product3 */

/* Model states */
static bool Chirp_Messung_Spule_X_Spannung_OK; /* Chirp_Messung_Spule/Spannung_OK */
static double Chirp_Messung_Spule_X_I_Filter_fg_500_; /* Chirp_Messung_Spule/I_Filter(fg=500) */
static bool Chirp_Messung_Spule_X_Monoflop; /* Chirp_Messung_Spule/Chirp/Monoflop */
static double Chirp_Messung_Spule_X_Delay; /* Chirp_Messung_Spule/Chirp/Sub/Delay */

#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
static double Chirp_Messung_Spule_ExtModeBuffer[5];
const double * const Chirp_Messung_Spule_ExtModeSignals[] = {
   &Chirp_Messung_Spule_B_ICDJL2_14,
   &Chirp_Messung_Spule_B_Sum,
   &Chirp_Messung_Spule_B_Spannung_OK,
   &Chirp_Messung_Spule_ExtModeBuffer[0],
   &Chirp_Messung_Spule_ExtModeBuffer[1],
   &Chirp_Messung_Spule_B_Product3,
   &Chirp_Messung_Spule_ExtModeBuffer[2],
   &Chirp_Messung_Spule_B_Gain1,
   &Chirp_Messung_Spule_ExtModeBuffer[3],
   &Chirp_Messung_Spule_B_Sum,
   &Chirp_Messung_Spule_B_Sum,
   &Chirp_Messung_Spule_B_IABJL2_16,
   &Chirp_Messung_Spule_B_ICDJL2_14,
   &Chirp_Messung_Spule_B_UZKJL2_8,
   &Chirp_Messung_Spule_B_Sum,
   &Chirp_Messung_Spule_ExtModeBuffer[4],
   &Chirp_Messung_Spule_B_ManualSwitch1,
   &Chirp_Messung_Spule_B_Switch,
   &Chirp_Messung_Spule_B_In1,
   &Chirp_Messung_Spule_B_Sum7
};
#endif /* defined(EXTERNAL_MODE) */
Chirp_Messung_Spule_Parameters Chirp_Messung_Spule_P = {
   /* Parameter 'SwitchState' of
    *  Manual Signal Switch : 'Chirp_Messung_Spule/Manual Switch1'
    */
   false
};
const char * Chirp_Messung_Spule_errorStatus;
const double Chirp_Messung_Spule_sampleTime = 2.00000000000000016e-05;
const char * const Chirp_Messung_Spule_checksum =
   "0b343723db4772c04c5d5c6f58d405821505b025";
/* Target declarations */
struct PlxDataCaptureRegistry plxDataCaptureRegistry[1];
const int plxUseEthercat = 0;
struct PlxProgrammableValueRegistry plxProgrammableValueRegistry[1];
struct PlxToFileRegistry plxToFileRegistry[1];
const char* plxAssertionMessages[] = {
   "","","","","","","","","","","","","","","","","","","","","","","","","",
   "","","","","","","",
};
void Chirp_Messung_Spule_initialize(double time)
{
   double remainder;
   Chirp_Messung_Spule_errorStatus = NULL;
   Chirp_Messung_Spule_tickHi =
      floor(time/(4294967296.0*Chirp_Messung_Spule_sampleTime));
   remainder = time - Chirp_Messung_Spule_tickHi*4294967296.0*
               Chirp_Messung_Spule_sampleTime;
   Chirp_Messung_Spule_tickLo = floor(
                                      remainder/Chirp_Messung_Spule_sampleTime +
                                      .5);
   remainder -= Chirp_Messung_Spule_tickLo*Chirp_Messung_Spule_sampleTime;
   if (fabs(remainder) > 1e-6*fabs(time))
   {
      Chirp_Messung_Spule_errorStatus =
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


   /* Initialization for Analog In : 'Chirp_Messung_Spule/UZK JL2_8' */
   setupAnalogIn(3, 2.100000000e+01f, 0.000000000e+00f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Analog In : 'Chirp_Messung_Spule/IAB JL2_16' */
   setupAnalogIn(4, 7.142857143e+00f, -1.071428571e+01f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Analog In : 'Chirp_Messung_Spule/ICD  JL2_14' */
   setupAnalogIn(5, 7.142857143e+00f, -1.071428571e+01f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Digital In : 'Chirp_Messung_Spule/Digital In4' */
   plxSetupDigitalInput(26, 3);

   /* Initialization for Relay : 'Chirp_Messung_Spule/Spannung_OK' */
   Chirp_Messung_Spule_X_Spannung_OK = 0;

   /* Initialization for Transfer Function : 'Chirp_Messung_Spule/I_Filter(fg=500)' */
   Chirp_Messung_Spule_X_I_Filter_fg_500_ = 0.;

   /* Initialization for Monoflop : 'Chirp_Messung_Spule/Chirp/Monoflop' */
   Chirp_Messung_Spule_X_Monoflop = 0.;
   Chirp_Messung_Spule_D_uint32_t[0] = 0;

   /* Initialization for Subsystem : 'Chirp_Messung_Spule/Chirp/Sub' */
   Chirp_Messung_Spule_X_Delay = 0.;
   Chirp_Messung_Spule_B_Sub = 0.;

   /* Initialization for Digital Out : 'Chirp_Messung_Spule/Enable1' */
   setupDigitalOut(12, DO_GPIO, DO_NINV);
   setupDigitalOut(13, DO_GPIO, DO_NINV);
   setupDigitalOut(14, DO_GPIO, DO_NINV);

   /* Initialization for PWM Out : 'Chirp_Messung_Spule/S J2' */
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

   /* Initialization for To File : 'Chirp_Messung_Spule/To File' */
   {
      plxSetupToFile(0, "DataLog", 3, 5000, 0, 2, 2, 0);
   }
}

void Chirp_Messung_Spule_step(void)
{
   if (Chirp_Messung_Spule_errorStatus)
   {
      return;
   }

   /* Analog In : 'Chirp_Messung_Spule/UZK JL2_8' */
   Chirp_Messung_Spule_B_UZKJL2_8 = getAnalogIn(3);

   /* Analog In : 'Chirp_Messung_Spule/IAB JL2_16' */
   Chirp_Messung_Spule_B_IABJL2_16 = getAnalogIn(4);

   /* Analog In : 'Chirp_Messung_Spule/ICD  JL2_14' */
   Chirp_Messung_Spule_B_ICDJL2_14 = getAnalogIn(5);

   /* Digital In : 'Chirp_Messung_Spule/Digital In4' */
   Chirp_Messung_Spule_B_DigitalIn4 = getDigitalIn(26);

   /* Saturation : 'Chirp_Messung_Spule/UZK_Nenner' */
   Chirp_Messung_Spule_B_UZK_Nenner = Chirp_Messung_Spule_B_UZKJL2_8;
   if (Chirp_Messung_Spule_B_UZK_Nenner < 1.)
   {
      Chirp_Messung_Spule_B_UZK_Nenner = 1.;
   }

   /* Relay : 'Chirp_Messung_Spule/Spannung_OK' */
   {
      double u = Chirp_Messung_Spule_B_UZKJL2_8;
      if (Chirp_Messung_Spule_X_Spannung_OK && u < 17.)
      {
         Chirp_Messung_Spule_X_Spannung_OK = 0;
      }
      else if (!Chirp_Messung_Spule_X_Spannung_OK && u > 18.)
      {
         Chirp_Messung_Spule_X_Spannung_OK = 1;
      }
   }
   Chirp_Messung_Spule_B_Spannung_OK =
      (Chirp_Messung_Spule_X_Spannung_OK) ? 1. : 0.;

   /* Logical Operator : 'Chirp_Messung_Spule/Freigabe' */
   Chirp_Messung_Spule_B_Freigabe = Chirp_Messung_Spule_B_DigitalIn4 &&
                                    Chirp_Messung_Spule_B_Spannung_OK;

   /* Sum : 'Chirp_Messung_Spule/Sum'
    * incorporates
    *  Transfer Function : 'Chirp_Messung_Spule/I_Filter(fg=500)'
    *  Constant : 'Chirp_Messung_Spule/I_Offset'
    */
   Chirp_Messung_Spule_B_Sum =
      (3124.99999999999955*
       Chirp_Messung_Spule_X_I_Filter_fg_500_) - (-0.0120000000000000002);

   /* Manual Signal Switch : 'Chirp_Messung_Spule/Manual Switch1'
    * incorporates
    *  Constant : 'Chirp_Messung_Spule/Trigger'
    *  Constant : 'Chirp_Messung_Spule/Trigger1'
    */
   Chirp_Messung_Spule_B_ManualSwitch1 =
      Chirp_Messung_Spule_P.ManualSwitch1_SwitchState ? 1. : 0.;

   /* Monoflop : 'Chirp_Messung_Spule/Chirp/Monoflop' */
   if (!Chirp_Messung_Spule_X_Monoflop &&
       (Chirp_Messung_Spule_B_ManualSwitch1))
   {
      Chirp_Messung_Spule_B_Monoflop = 1;
      Chirp_Messung_Spule_D_uint32_t[0] = 1025000;
   }
   else if (Chirp_Messung_Spule_D_uint32_t[0] == 0)
   {
      Chirp_Messung_Spule_B_Monoflop = 0;
   }

   /* Subsystem : 'Chirp_Messung_Spule/Chirp/Sub' */
   {

      /* Delay : 'Chirp_Messung_Spule/Chirp/Sub/Delay' */
      Chirp_Messung_Spule_B_Delay = Chirp_Messung_Spule_X_Delay;

      /* Sum : 'Chirp_Messung_Spule/Chirp/Sub/Sum7'
       * incorporates
       *  Constant : 'Chirp_Messung_Spule/Chirp/Sub/offs3'
       */
      Chirp_Messung_Spule_B_Sum7 = 2.00000000000000016e-05 +
                                   Chirp_Messung_Spule_B_Delay;

      /* Signal Inport : 'Chirp_Messung_Spule/Chirp/Sub/In1' */
      Chirp_Messung_Spule_B_In1 = (double)Chirp_Messung_Spule_B_Monoflop;

      /* Signal Switch : 'Chirp_Messung_Spule/Chirp/Sub/Switch'
       * incorporates
       *  Constant : 'Chirp_Messung_Spule/Chirp/Sub/offs4'
       */
      Chirp_Messung_Spule_B_Switch =
         (Chirp_Messung_Spule_B_In1 > 0.) ? Chirp_Messung_Spule_B_Sum7 : 0.;
      Chirp_Messung_Spule_B_Sub = Chirp_Messung_Spule_B_Delay;
   }

   /* Logical Operator : 'Chirp_Messung_Spule/Chirp/Logical\nOperator'
    * incorporates
    *  Relational Operator : 'Chirp_Messung_Spule/Chirp/Relational\nOperator1'
    *  Constant : 'Chirp_Messung_Spule/Chirp/T0'
    *  Relational Operator : 'Chirp_Messung_Spule/Chirp/Relational\nOperator2'
    *  Sum : 'Chirp_Messung_Spule/Chirp/Sum1'
    */
   Chirp_Messung_Spule_B_LogicalOperator =
      (Chirp_Messung_Spule_B_Sub > 0.5) && (Chirp_Messung_Spule_B_Sub < 20.5);

   /* Gain : 'Chirp_Messung_Spule/Gain1'
    * incorporates
    *  Signal Switch : 'Chirp_Messung_Spule/Chirp/Switch'
    *  Sum : 'Chirp_Messung_Spule/Chirp/Sum6'
    *  Signal Switch : 'Chirp_Messung_Spule/Chirp/Switch1'
    *  Gain : 'Chirp_Messung_Spule/Chirp/Gain'
    *  Trigonometric Function : 'Chirp_Messung_Spule/Chirp/Trigonometric\nFunction'
    *  Function : 'Chirp_Messung_Spule/Chirp/Fcn'
    *  Constant : 'Chirp_Messung_Spule/Chirp/f1'
    *  Math Function : 'Chirp_Messung_Spule/Chirp/Math'
    *  Sum : 'Chirp_Messung_Spule/Chirp/Sum5'
    *  Constant : 'Chirp_Messung_Spule/Chirp/T0'
    *  Constant : 'Chirp_Messung_Spule/Chirp/Tm'
    *  Constant : 'Chirp_Messung_Spule/Chirp/offs1'
    *  Constant : 'Chirp_Messung_Spule/Chirp/offs'
    */
   Chirp_Messung_Spule_B_Gain1 = 1.*
                                 ((Chirp_Messung_Spule_B_Monoflop >
                                   false) ? (((
                                               Chirp_Messung_Spule_B_LogicalOperator
                                               > false) ? (8.*
                                                           sin(
                                                               9.74196174945579152
                                                               *
                                                               ((
                                                                 0.0500000000000000028
                                                                 *
                                                                 pow(
                                                                     400000.,
                                                                     plecsmod(
                                                                              Chirp_Messung_Spule_B_Sub
                                                                              -
   0.5,
                                                                              20.)
                                                                     /
                                                                     20.))-
   0.0500000000000000028))) : 0.) + 0.) : 0.);

   /* Product : 'Chirp_Messung_Spule/Product3' */
   Chirp_Messung_Spule_B_Product3 = 1. / Chirp_Messung_Spule_B_UZK_Nenner *
                                    Chirp_Messung_Spule_B_Gain1;
   /* Digital Out : 'Chirp_Messung_Spule/Enable1' */
   writeDigitalOut(12, Chirp_Messung_Spule_B_Freigabe);
   writeDigitalOut(13, Chirp_Messung_Spule_B_Freigabe);
   writeDigitalOut(14, Chirp_Messung_Spule_B_Freigabe);
   /* Saturation : 'Chirp_Messung_Spule/Saturation' */
   Chirp_Messung_Spule_B_Saturation[0] = Chirp_Messung_Spule_B_Product3;
   if (Chirp_Messung_Spule_B_Saturation[0] > 0.900000000000000022)
   {
      Chirp_Messung_Spule_B_Saturation[0] = 0.900000000000000022;
   }
   else if (Chirp_Messung_Spule_B_Saturation[0] < -0.900000000000000022)
   {
      Chirp_Messung_Spule_B_Saturation[0] = -0.900000000000000022;
   }
   Chirp_Messung_Spule_B_Saturation[1] = Chirp_Messung_Spule_B_Product3;
   if (Chirp_Messung_Spule_B_Saturation[1] > 0.900000000000000022)
   {
      Chirp_Messung_Spule_B_Saturation[1] = 0.900000000000000022;
   }
   else if (Chirp_Messung_Spule_B_Saturation[1] < -0.900000000000000022)
   {
      Chirp_Messung_Spule_B_Saturation[1] = -0.900000000000000022;
   }
   Chirp_Messung_Spule_B_Saturation[2] = Chirp_Messung_Spule_B_Product3;
   if (Chirp_Messung_Spule_B_Saturation[2] > 0.900000000000000022)
   {
      Chirp_Messung_Spule_B_Saturation[2] = 0.900000000000000022;
   }
   else if (Chirp_Messung_Spule_B_Saturation[2] < -0.900000000000000022)
   {
      Chirp_Messung_Spule_B_Saturation[2] = -0.900000000000000022;
   }
   Chirp_Messung_Spule_B_Saturation[3] = Chirp_Messung_Spule_B_Product3;
   if (Chirp_Messung_Spule_B_Saturation[3] > 0.900000000000000022)
   {
      Chirp_Messung_Spule_B_Saturation[3] = 0.900000000000000022;
   }
   else if (Chirp_Messung_Spule_B_Saturation[3] < -0.900000000000000022)
   {
      Chirp_Messung_Spule_B_Saturation[3] = -0.900000000000000022;
   }

   /* PWM Out : 'Chirp_Messung_Spule/S J2' */
   {
      const int periodPWM_int = 1334;
      const float gain = 6.667500000e+02f;
      {
         int cmpPWM =
            (int)(((Chirp_Messung_Spule_B_Saturation[0]) +
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
            (int)(((Chirp_Messung_Spule_B_Saturation[1]) +
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
            (int)(((Chirp_Messung_Spule_B_Saturation[2]) +
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
            (int)(((Chirp_Messung_Spule_B_Saturation[3]) +
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

   /* To File : 'Chirp_Messung_Spule/To File' */
   {
      float data[] = {
         Chirp_Messung_Spule_B_Gain1, Chirp_Messung_Spule_B_Sum,
         ((double)Chirp_Messung_Spule_B_LogicalOperator)
      };
      plxUpdateToFile(0, data);
   }

#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
   Chirp_Messung_Spule_ExtModeBuffer[0] =
      (double)Chirp_Messung_Spule_B_Freigabe;
   Chirp_Messung_Spule_ExtModeBuffer[1] =
      (double)Chirp_Messung_Spule_B_DigitalIn4;
   Chirp_Messung_Spule_ExtModeBuffer[2] =
      (double)Chirp_Messung_Spule_B_LogicalOperator;
   Chirp_Messung_Spule_ExtModeBuffer[3] =
      (double)Chirp_Messung_Spule_B_LogicalOperator;
   Chirp_Messung_Spule_ExtModeBuffer[4] =
      (double)Chirp_Messung_Spule_B_Monoflop;
#endif /* defined(EXTERNAL_MODE) */

   if (Chirp_Messung_Spule_errorStatus)
   {
      return;
   }

   /* Update for Monoflop : 'Chirp_Messung_Spule/Chirp/Monoflop' */
   if (Chirp_Messung_Spule_D_uint32_t[0] > 0)
   {
      Chirp_Messung_Spule_D_uint32_t[0] -= 1;
   }
   Chirp_Messung_Spule_X_Monoflop = Chirp_Messung_Spule_B_ManualSwitch1;

   /* Update for Subsystem : 'Chirp_Messung_Spule/Chirp/Sub' */
   {

      /* Update for Delay : 'Chirp_Messung_Spule/Chirp/Sub/Delay' */
      Chirp_Messung_Spule_X_Delay = Chirp_Messung_Spule_B_Switch;
   }

   /* Derivatives for Transfer Function : 'Chirp_Messung_Spule/I_Filter(fg=500)'
    * incorporates
    *  Sum : 'Chirp_Messung_Spule/Sum1'
    */
   Chirp_Messung_Spule_deriv[0] =
      (Chirp_Messung_Spule_B_IABJL2_16 +
       Chirp_Messung_Spule_B_ICDJL2_14)-3124.99999999999955*
      Chirp_Messung_Spule_X_I_Filter_fg_500_;

   /* Update continuous states */
   Chirp_Messung_Spule_X_I_Filter_fg_500_ += 2.00000000000000016e-05*
                                             Chirp_Messung_Spule_deriv[0];
}

void Chirp_Messung_Spule_terminate(void)
{
}
