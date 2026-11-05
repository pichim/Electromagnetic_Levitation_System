/*
 * Implementation file for: Stromregler_und_Hoehenregler_RTBox
 * Generated with         : PLECS 5.0.6
 *                          PLECS RT Box 1 4.0.8
 * Generated on           : 5 Nov 2026 16:58:06
 */
#include "Stromregler_und_Hoehenregler_RTBox.h"
#ifndef PLECS_HEADER_Stromregler_und_Hoehenregler_RTBox_h_
#error The wrong header file "Stromregler_und_Hoehenregler_RTBox.h" was
#error included. Please check your include path to see whether this file
#error name conflicts with the name of another header file.
#endif /* PLECS_HEADER_Stromregler_und_Hoehenregler_RTBox_h_ */
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
#include <stdlib.h>
#define PLECSRunTimeError(msg) Stromregler_und_Hoehenregler_RTBox_errorStatus \
      = msg
struct CScriptStruct
{
   int numInputTerminals;
   int numOutputTerminals;
   const int* numInputSignals;
   const int* numOutputSignals;
   int numContStates;
   int numDiscStates;
   int numZCSignals;
   int numSampleTimes;
   int numParameters;
   int isMajorTimeStep;
   int isRefineStep;
   double time;
   const double * const * const *inputs;
   double * const * const *outputs;
   double *contStates;
   double *contDerivs;
   double *discStates;
   double *zCSignals;
   const int *paramNumDims;
   const int * const *paramDims;
   const int *paramNumElements;
   const double * const *paramRealData;
   const char * const *paramStringData;
   const char * const *sampleHits;
   const double *sampleTimePeriods;
   const double *sampleTimeOffsets;
   const double * const *inputSampleTimePeriods;
   const double * const *inputSampleTimeOffsets;
   double *nextSampleHit;
   const char** errorStatus;
   const char** warningStatus;
   const char** rangeErrorMsg;
   int* rangeErrorLine;
   void (*writeCustomStateDouble)(void*, double);
   double (*readCustomStateDouble)(void*);
   void (*writeCustomStateInt)(void*, int);
   void (*writeCustomStateData)(void*, const void*, int);
   void (*readCustomStateData)(void*, void*, int);
};
static struct CScriptStruct Stromregler_und_Hoehenregler_RTBox_cScriptStruct[2
];
static char Stromregler_und_Hoehenregler_RTBox_isMajorStep = '\001';
static const uint32_t Stromregler_und_Hoehenregler_RTBox_subTaskPeriod[1]= {
   /* [4e-05, 0], [0, 0] */
   2
};
static uint32_t Stromregler_und_Hoehenregler_RTBox_subTaskTick[1];
static char Stromregler_und_Hoehenregler_RTBox_subTaskHit[1];
#define Stromregler_und_Hoehenregler_RTBox_UNCONNECTED 0
static double Stromregler_und_Hoehenregler_RTBox_deriv[2] _ALIGN;
void Stromregler_und_Hoehenregler_RTBox_0_cScriptStart(
                                                       const struct CScriptStruct *cScriptStruct);
void Stromregler_und_Hoehenregler_RTBox_0_cScriptOutput(
                                                        const struct CScriptStruct *cScriptStruct);
void Stromregler_und_Hoehenregler_RTBox_0_cScriptUpdate(
                                                        const struct CScriptStruct *cScriptStruct);
void Stromregler_und_Hoehenregler_RTBox_0_cScriptDerivative(
                                                            const struct CScriptStruct *cScriptStruct);
void Stromregler_und_Hoehenregler_RTBox_0_cScriptTerminate(
                                                           const struct CScriptStruct *cScriptStruct);
void Stromregler_und_Hoehenregler_RTBox_1_cScriptStart(
                                                       const struct CScriptStruct *cScriptStruct);
void Stromregler_und_Hoehenregler_RTBox_1_cScriptOutput(
                                                        const struct CScriptStruct *cScriptStruct);
void Stromregler_und_Hoehenregler_RTBox_1_cScriptUpdate(
                                                        const struct CScriptStruct *cScriptStruct);
void Stromregler_und_Hoehenregler_RTBox_1_cScriptDerivative(
                                                            const struct CScriptStruct *cScriptStruct);
void Stromregler_und_Hoehenregler_RTBox_1_cScriptTerminate(
                                                           const struct CScriptStruct *cScriptStruct);
static uint32_t Stromregler_und_Hoehenregler_RTBox_tickLo;
static int32_t Stromregler_und_Hoehenregler_RTBox_tickHi;
/* Block outputs */
static double Stromregler_und_Hoehenregler_RTBox_B_UZK_Nenner; /* Stromregler_und_Hoehenregler_RTBox/UZK_Nenner */
static double Stromregler_und_Hoehenregler_RTBox_B_Ball_Detection; /* Stromregler_und_Hoehenregler_RTBox/Ball_Detection */
static double Stromregler_und_Hoehenregler_RTBox_B_Median_Hoehe; /* Stromregler_und_Hoehenregler_RTBox/Median_Hoehe */
static double Stromregler_und_Hoehenregler_RTBox_B_Sum3; /* Stromregler_und_Hoehenregler_RTBox/Sum3 */
static double Stromregler_und_Hoehenregler_RTBox_B_Saturation1; /* Stromregler_und_Hoehenregler_RTBox/Saturation1 */
static double Stromregler_und_Hoehenregler_RTBox_B_K_U_I; /* Stromregler_und_Hoehenregler_RTBox/K_U_I */
static double Stromregler_und_Hoehenregler_RTBox_B_I_Soll_Begrenzung; /* Stromregler_und_Hoehenregler_RTBox/I_Soll_Begrenzung */
static double Stromregler_und_Hoehenregler_RTBox_B_ManualSwitch; /* Stromregler_und_Hoehenregler_RTBox/Manual Switch */
static double Stromregler_und_Hoehenregler_RTBox_B_Saturation; /* Stromregler_und_Hoehenregler_RTBox/Continuous PID Controller3/Saturation/internal/Saturation Select/constant/Saturation */
static double Stromregler_und_Hoehenregler_RTBox_B_Hoehenregler_500Hz; /* Stromregler_und_Hoehenregler_RTBox/Hoehenregler_500Hz */
static double Stromregler_und_Hoehenregler_RTBox_B_Min_Max; /* Stromregler_und_Hoehenregler_RTBox/Continuous PID Controller3/Anti-windup method/Conditional Integration/Dead Zone4/Min/Max */
static double Stromregler_und_Hoehenregler_RTBox_B_Min_Max1; /* Stromregler_und_Hoehenregler_RTBox/Continuous PID Controller3/Anti-windup method/Conditional Integration/Dead Zone4/Min/Max1 */
static bool Stromregler_und_Hoehenregler_RTBox_B_RelationalOperator; /* Stromregler_und_Hoehenregler_RTBox/Continuous PID Controller3/Anti-windup method/Conditional Integration/Relational Operator */
static double Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[4]; /* Stromregler_und_Hoehenregler_RTBox/Saturation */
static double Stromregler_und_Hoehenregler_RTBox_B_UZKJL2_8; /* Stromregler_und_Hoehenregler_RTBox/UZK JL2_8 */
static double Stromregler_und_Hoehenregler_RTBox_B_IABJL2_16; /* Stromregler_und_Hoehenregler_RTBox/IAB JL2_16 */
static double Stromregler_und_Hoehenregler_RTBox_B_ICDJL2_14; /* Stromregler_und_Hoehenregler_RTBox/ICD  JL2_14 */
static bool Stromregler_und_Hoehenregler_RTBox_B_DigitalIn4; /* Stromregler_und_Hoehenregler_RTBox/Digital In4 */
static double Stromregler_und_Hoehenregler_RTBox_B_U_Laser; /* Stromregler_und_Hoehenregler_RTBox/U_Laser */
static double Stromregler_und_Hoehenregler_RTBox_B_Spannung_OK; /* Stromregler_und_Hoehenregler_RTBox/Spannung_OK */
static bool Stromregler_und_Hoehenregler_RTBox_B_Freigabe; /* Stromregler_und_Hoehenregler_RTBox/Freigabe */
static bool Stromregler_und_Hoehenregler_RTBox_B_Reset_PI; /* Stromregler_und_Hoehenregler_RTBox/Reset_PI */
static double Stromregler_und_Hoehenregler_RTBox_B_Integrator1; /* Stromregler_und_Hoehenregler_RTBox/Continuous PID Controller3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1 */
static double Stromregler_und_Hoehenregler_RTBox_B_Sum; /* Stromregler_und_Hoehenregler_RTBox/Sum */
static double Stromregler_und_Hoehenregler_RTBox_B_Sum2; /* Stromregler_und_Hoehenregler_RTBox/Sum2 */
static double Stromregler_und_Hoehenregler_RTBox_B_Subtract2; /* Stromregler_und_Hoehenregler_RTBox/Subtract2 */
static double Stromregler_und_Hoehenregler_RTBox_B_Sum_1; /* Stromregler_und_Hoehenregler_RTBox/Continuous PID Controller3/Continous Time/Sum */
static double Stromregler_und_Hoehenregler_RTBox_B_Product3; /* Stromregler_und_Hoehenregler_RTBox/Product3 */
static double Stromregler_und_Hoehenregler_RTBox_B_Sum_2; /* Stromregler_und_Hoehenregler_RTBox/Continuous PID Controller3/Anti-windup method/Conditional Integration/Sum */
static double Stromregler_und_Hoehenregler_RTBox_B_Sum1; /* Stromregler_und_Hoehenregler_RTBox/Continuous PID Controller3/Anti-windup method/Conditional Integration/Sum1 */

/* Model states */
static bool Stromregler_und_Hoehenregler_RTBox_X_Spannung_OK; /* Stromregler_und_Hoehenregler_RTBox/Spannung_OK */
static double Stromregler_und_Hoehenregler_RTBox_X_Integrator1_x; /* Stromregler_und_Hoehenregler_RTBox/Continuous PID Controller3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1 */
static bool Stromregler_und_Hoehenregler_RTBox_X_Integrator1_i1_first; /* Stromregler_und_Hoehenregler_RTBox/Continuous PID Controller3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1 */
static double Stromregler_und_Hoehenregler_RTBox_X_I_Filter_fg_500_; /* Stromregler_und_Hoehenregler_RTBox/I_Filter(fg=500) */
static double Stromregler_und_Hoehenregler_RTBox_X_Ball_Detection[2]; /* Stromregler_und_Hoehenregler_RTBox/Ball_Detection */
static double Stromregler_und_Hoehenregler_RTBox_X_Median_Hoehe[3]; /* Stromregler_und_Hoehenregler_RTBox/Median_Hoehe */
static double Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[3]; /* Stromregler_und_Hoehenregler_RTBox/Hoehenregler_500Hz */

#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
static double Stromregler_und_Hoehenregler_RTBox_ExtModeBuffer[2];
const double * const Stromregler_und_Hoehenregler_RTBox_ExtModeSignals[] = {
   &Stromregler_und_Hoehenregler_RTBox_B_Ball_Detection,
   &Stromregler_und_Hoehenregler_RTBox_B_ICDJL2_14,
   &Stromregler_und_Hoehenregler_RTBox_B_Sum,
   &Stromregler_und_Hoehenregler_RTBox_B_Spannung_OK,
   &Stromregler_und_Hoehenregler_RTBox_B_Saturation,
   &Stromregler_und_Hoehenregler_RTBox_ExtModeBuffer[0],
   &Stromregler_und_Hoehenregler_RTBox_ExtModeBuffer[1],
   &Stromregler_und_Hoehenregler_RTBox_B_Product3,
   &Stromregler_und_Hoehenregler_RTBox_B_U_Laser,
   &Stromregler_und_Hoehenregler_RTBox_B_Sum2,
   &Stromregler_und_Hoehenregler_RTBox_B_Sum3,
   &Stromregler_und_Hoehenregler_RTBox_B_Sum2,
   &Stromregler_und_Hoehenregler_RTBox_B_Ball_Detection,
   &Stromregler_und_Hoehenregler_RTBox_B_Hoehenregler_500Hz,
   &Stromregler_und_Hoehenregler_RTBox_B_I_Soll_Begrenzung,
   &Stromregler_und_Hoehenregler_RTBox_B_Saturation,
   &Stromregler_und_Hoehenregler_RTBox_B_Product3,
   &Stromregler_und_Hoehenregler_RTBox_B_Product3,
   &Stromregler_und_Hoehenregler_RTBox_B_Product3,
   &Stromregler_und_Hoehenregler_RTBox_B_Product3,
   &Stromregler_und_Hoehenregler_RTBox_B_I_Soll_Begrenzung,
   &Stromregler_und_Hoehenregler_RTBox_B_Sum,
   &Stromregler_und_Hoehenregler_RTBox_B_Sum2,
   &Stromregler_und_Hoehenregler_RTBox_B_Saturation,
   &Stromregler_und_Hoehenregler_RTBox_B_Sum,
   &Stromregler_und_Hoehenregler_RTBox_B_IABJL2_16,
   &Stromregler_und_Hoehenregler_RTBox_B_ICDJL2_14,
   &Stromregler_und_Hoehenregler_RTBox_B_UZKJL2_8,
   &Stromregler_und_Hoehenregler_RTBox_B_Hoehenregler_500Hz,
   &Stromregler_und_Hoehenregler_RTBox_B_Sum
};
#endif /* defined(EXTERNAL_MODE) */
Stromregler_und_Hoehenregler_RTBox_Parameters
   Stromregler_und_Hoehenregler_RTBox_P = {
   /* Parameter 'K' of
    *  Gain : 'Stromregler_und_Hoehenregler_RTBox/K_U_I'
    */
   -0.800000000000000044,
   /* Parameter 'SwitchState' of
    *  Manual Signal Switch : 'Stromregler_und_Hoehenregler_RTBox/Manual Switch'
    */
   false
};
const char * Stromregler_und_Hoehenregler_RTBox_errorStatus;
const double Stromregler_und_Hoehenregler_RTBox_sampleTime =
   2.00000000000000016e-05;
const char * const Stromregler_und_Hoehenregler_RTBox_checksum =
   "27e9fc48b0281dbc6e7d435f781e1d6cdc469ddf";
/* Target declarations */
struct PlxDataCaptureRegistry plxDataCaptureRegistry[1];
const int plxUseEthercat = 0;
struct PlxProgrammableValueRegistry plxProgrammableValueRegistry[1];
struct PlxToFileRegistry plxToFileRegistry[1];
const char* plxAssertionMessages[] = {
   "","","","","","","","","","","","","","","","","","","","","","","","","",
   "","","","","","","",
};
void Stromregler_und_Hoehenregler_RTBox_initialize(double time)
{
   double remainder;
   Stromregler_und_Hoehenregler_RTBox_errorStatus = NULL;
   Stromregler_und_Hoehenregler_RTBox_tickHi =
      floor(time/
            (4294967296.0*Stromregler_und_Hoehenregler_RTBox_sampleTime));
   remainder = time - Stromregler_und_Hoehenregler_RTBox_tickHi*4294967296.0*
               Stromregler_und_Hoehenregler_RTBox_sampleTime;
   Stromregler_und_Hoehenregler_RTBox_tickLo = floor(
                                                     remainder/Stromregler_und_Hoehenregler_RTBox_sampleTime +
                                                     .5);
   remainder -= Stromregler_und_Hoehenregler_RTBox_tickLo*
                Stromregler_und_Hoehenregler_RTBox_sampleTime;
   if (fabs(remainder) > 1e-6*fabs(time))
   {
      Stromregler_und_Hoehenregler_RTBox_errorStatus =
         "Start time must be an integer multiple of the base sample time.";
   }
   /* Initialize sub-task tick counters */
   Stromregler_und_Hoehenregler_RTBox_subTaskTick[0] = 0; /* [0, 0], [4e-05, 0] */


   /* Offset sub-task tick counters */
   {
      uint32_t i, n, N, delta;
      N = abs(Stromregler_und_Hoehenregler_RTBox_tickHi);
      for (i = 0; i < 1; ++i)
      {
         delta = -Stromregler_und_Hoehenregler_RTBox_subTaskPeriod[i];
         delta %= Stromregler_und_Hoehenregler_RTBox_subTaskPeriod[i];
         if (Stromregler_und_Hoehenregler_RTBox_tickHi < 0)
         {
            delta = Stromregler_und_Hoehenregler_RTBox_subTaskPeriod[i] -
                    delta;
         }
         for (n = 0; n < N; ++n)
         {
            Stromregler_und_Hoehenregler_RTBox_subTaskTick[i] =
               (Stromregler_und_Hoehenregler_RTBox_subTaskTick[i] +
                delta) % Stromregler_und_Hoehenregler_RTBox_subTaskPeriod[i];
         }
         Stromregler_und_Hoehenregler_RTBox_subTaskTick[i] =
            (Stromregler_und_Hoehenregler_RTBox_subTaskTick[i] +
             Stromregler_und_Hoehenregler_RTBox_tickLo %
             Stromregler_und_Hoehenregler_RTBox_subTaskPeriod[i]) %
            Stromregler_und_Hoehenregler_RTBox_subTaskPeriod[i];
      }
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


   /* Initialization for Analog In : 'Stromregler_und_Hoehenregler_RTBox/UZK JL2_8' */
   setupAnalogIn(3, 2.100000000e+01f, 0.000000000e+00f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Analog In : 'Stromregler_und_Hoehenregler_RTBox/IAB JL2_16' */
   setupAnalogIn(4, 7.142857143e+00f, -1.071428571e+01f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Analog In : 'Stromregler_und_Hoehenregler_RTBox/ICD  JL2_14' */
   setupAnalogIn(5, 7.142857143e+00f, -1.071428571e+01f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Digital In : 'Stromregler_und_Hoehenregler_RTBox/Digital In4' */
   plxSetupDigitalInput(26, 3);

   /* Initialization for Analog In : 'Stromregler_und_Hoehenregler_RTBox/U_Laser' */
   setupAnalogIn(0, 1.000000000e+00f, 0.000000000e+00f, 0, 0,
                 0.000000000e+00f, 0.000000000e+00f);

   /* Initialization for Relay : 'Stromregler_und_Hoehenregler_RTBox/Spannung_OK' */
   Stromregler_und_Hoehenregler_RTBox_X_Spannung_OK = 0;

   /* Initialization for Integrator : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1' */
   Stromregler_und_Hoehenregler_RTBox_X_Integrator1_x = 0;
   Stromregler_und_Hoehenregler_RTBox_X_Integrator1_i1_first = 1;

   /* Initialization for Transfer Function : 'Stromregler_und_Hoehenregler_RTBox/I_Filter(fg=500)' */
   Stromregler_und_Hoehenregler_RTBox_X_I_Filter_fg_500_ = 0.;

   /* Initialization for C-Script : 'Stromregler_und_Hoehenregler_RTBox/Ball_Detection' */
   {
      static const int numInputSignals[] = {
         1
      };
      static const double* const inputPtrs[] = {
         &Stromregler_und_Hoehenregler_RTBox_B_Sum2
      };
      static const double* const * const inputs[] = {
         &inputPtrs[0]
      };
      static const int numOutputSignals[] = {
         1
      };
      static double* const outputPtrs[] = {
         &Stromregler_und_Hoehenregler_RTBox_B_Ball_Detection
      };
      static double* const * const outputs[] = {
         &outputPtrs[0]
      };
      static double nextSampleHit;
      static const char * const sampleHits[] = {
         &Stromregler_und_Hoehenregler_RTBox_isMajorStep
      };
      static const double sampleTimePeriods[] = {
         2e-05
      };
      static const double sampleTimeOffsets[] = {
         0
      };
      static const double terminalSampleTimePeriods[] = {
         0.
      };
      static const double terminalSampleTimeOffsets[] = {
         -1.
      };
      static const double* const terminalSampleTimePeriodPtrs[] = {
         &terminalSampleTimePeriods[0]
      };
      static const double* const terminalSampleTimeOffsetPtrs[] = {
         &terminalSampleTimeOffsets[0]
      };
      static const char* errorStatus;
      static const char* warningStatus;
      static const char* rangeErrorMsg;
      static const double paramData[] = {
         25000.
      };
      static const double* const paramDataPtr[] = {
         paramData+0
      };
      static const char paramStringData[] = "\0";
      static const char* const paramStringDataPtr[] = {
         paramStringData+0
      };
      static const int paramDim[] = {
         1,1
      };
      static const int* const paramDimPtr[] = {
         paramDim+0
      };
      static const int paramNumElements[] = {
         1
      };
      static const int paramNumDims[] = {
         2
      };
      errorStatus = NULL;
      warningStatus = NULL;
      rangeErrorMsg = NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].isMajorTimeStep = 1;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].isRefineStep = 0;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].numInputTerminals =
         1;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].numInputSignals =
         numInputSignals;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].inputs = inputs;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].numOutputTerminals =
         1;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].numOutputSignals =
         numOutputSignals;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].outputs = outputs;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].numContStates = 0;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].contStates = NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].contDerivs = NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].numDiscStates = 2;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].discStates =
         &Stromregler_und_Hoehenregler_RTBox_X_Ball_Detection[0];
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].numZCSignals = 0;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].numParameters = 1;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].paramNumDims =
         paramNumDims;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].paramDims =
         paramDimPtr;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].paramNumElements =
         paramNumElements;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].paramRealData =
         paramDataPtr;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].paramStringData =
         paramStringDataPtr;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].numSampleTimes = 1;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].sampleTimePeriods =
         sampleTimePeriods;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].sampleTimeOffsets =
         sampleTimeOffsets;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].
      inputSampleTimePeriods = terminalSampleTimePeriodPtrs;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].
      inputSampleTimeOffsets = terminalSampleTimeOffsetPtrs;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].sampleHits =
         sampleHits;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].nextSampleHit =
         &nextSampleHit;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].errorStatus =
         &errorStatus;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].warningStatus =
         &warningStatus;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].rangeErrorMsg =
         &rangeErrorMsg;
      Stromregler_und_Hoehenregler_RTBox_0_cScriptStart(
                                                        &Stromregler_und_Hoehenregler_RTBox_cScriptStruct[
                                                           0]);
      if (*Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].errorStatus)
         Stromregler_und_Hoehenregler_RTBox_errorStatus =
            *Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].errorStatus;
   }

   /* Initialization for C-Script : 'Stromregler_und_Hoehenregler_RTBox/Median_Hoehe' */
   {
      static const int numInputSignals[] = {
         1
      };
      static const double* const inputPtrs[] = {
         &Stromregler_und_Hoehenregler_RTBox_B_Sum2
      };
      static const double* const * const inputs[] = {
         &inputPtrs[0]
      };
      static const int numOutputSignals[] = {
         1
      };
      static double* const outputPtrs[] = {
         &Stromregler_und_Hoehenregler_RTBox_B_Median_Hoehe
      };
      static double* const * const outputs[] = {
         &outputPtrs[0]
      };
      static double nextSampleHit;
      static const char * const sampleHits[] = {
         &Stromregler_und_Hoehenregler_RTBox_subTaskHit[0]
      };
      static const double sampleTimePeriods[] = {
         4e-05
      };
      static const double sampleTimeOffsets[] = {
         0
      };
      static const double terminalSampleTimePeriods[] = {
         0.
      };
      static const double terminalSampleTimeOffsets[] = {
         -1.
      };
      static const double* const terminalSampleTimePeriodPtrs[] = {
         &terminalSampleTimePeriods[0]
      };
      static const double* const terminalSampleTimeOffsetPtrs[] = {
         &terminalSampleTimeOffsets[0]
      };
      static const char* errorStatus;
      static const char* warningStatus;
      static const char* rangeErrorMsg;
      errorStatus = NULL;
      warningStatus = NULL;
      rangeErrorMsg = NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].isMajorTimeStep = 1;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].isRefineStep = 0;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].numInputTerminals =
         1;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].numInputSignals =
         numInputSignals;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].inputs = inputs;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].numOutputTerminals =
         1;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].numOutputSignals =
         numOutputSignals;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].outputs = outputs;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].numContStates = 0;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].contStates = NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].contDerivs = NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].numDiscStates = 3;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].discStates =
         &Stromregler_und_Hoehenregler_RTBox_X_Median_Hoehe[0];
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].numZCSignals = 0;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].numParameters = 0;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].paramNumDims = NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].paramDims = NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].paramNumElements =
         NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].paramRealData =
         NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].paramStringData =
         NULL;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].numSampleTimes = 1;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].sampleTimePeriods =
         sampleTimePeriods;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].sampleTimeOffsets =
         sampleTimeOffsets;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].
      inputSampleTimePeriods = terminalSampleTimePeriodPtrs;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].
      inputSampleTimeOffsets = terminalSampleTimeOffsetPtrs;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].sampleHits =
         sampleHits;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].nextSampleHit =
         &nextSampleHit;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].errorStatus =
         &errorStatus;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].warningStatus =
         &warningStatus;
      Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].rangeErrorMsg =
         &rangeErrorMsg;
      Stromregler_und_Hoehenregler_RTBox_1_cScriptStart(
                                                        &Stromregler_und_Hoehenregler_RTBox_cScriptStruct[
                                                           1]);
      if (*Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].errorStatus)
         Stromregler_und_Hoehenregler_RTBox_errorStatus =
            *Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].errorStatus;
   }

   /* Initialization for Discrete Transfer Function : 'Stromregler_und_Hoehenregler_RTBox/Hoehenregler_500Hz' */
   Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[0] = 0.;
   Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[1] = 0.;
   Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[2] = 0.;

   /* Initialization for Digital Out : 'Stromregler_und_Hoehenregler_RTBox/Enable1' */
   setupDigitalOut(12, DO_GPIO, DO_NINV);
   setupDigitalOut(13, DO_GPIO, DO_NINV);
   setupDigitalOut(14, DO_GPIO, DO_NINV);

   /* Initialization for PWM Out : 'Stromregler_und_Hoehenregler_RTBox/S J2' */
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

void Stromregler_und_Hoehenregler_RTBox_step(void)
{
   if (Stromregler_und_Hoehenregler_RTBox_errorStatus)
   {
      return;
   }
   {
      size_t i;
      for (i = 0; i < 1; ++i)
      {
         Stromregler_und_Hoehenregler_RTBox_subTaskHit[i] =
            (Stromregler_und_Hoehenregler_RTBox_subTaskTick[i] == 0);
      }
   }

   /* Analog In : 'Stromregler_und_Hoehenregler_RTBox/UZK JL2_8' */
   Stromregler_und_Hoehenregler_RTBox_B_UZKJL2_8 = getAnalogIn(3);

   /* Analog In : 'Stromregler_und_Hoehenregler_RTBox/IAB JL2_16' */
   Stromregler_und_Hoehenregler_RTBox_B_IABJL2_16 = getAnalogIn(4);

   /* Analog In : 'Stromregler_und_Hoehenregler_RTBox/ICD  JL2_14' */
   Stromregler_und_Hoehenregler_RTBox_B_ICDJL2_14 = getAnalogIn(5);

   /* Digital In : 'Stromregler_und_Hoehenregler_RTBox/Digital In4' */
   Stromregler_und_Hoehenregler_RTBox_B_DigitalIn4 = getDigitalIn(26);

   /* Analog In : 'Stromregler_und_Hoehenregler_RTBox/U_Laser' */
   Stromregler_und_Hoehenregler_RTBox_B_U_Laser = getAnalogIn(0);

   /* Saturation : 'Stromregler_und_Hoehenregler_RTBox/UZK_Nenner' */
   Stromregler_und_Hoehenregler_RTBox_B_UZK_Nenner =
      Stromregler_und_Hoehenregler_RTBox_B_UZKJL2_8;
   if (Stromregler_und_Hoehenregler_RTBox_B_UZK_Nenner < 1.)
   {
      Stromregler_und_Hoehenregler_RTBox_B_UZK_Nenner = 1.;
   }

   /* Relay : 'Stromregler_und_Hoehenregler_RTBox/Spannung_OK' */
   {
      double u = Stromregler_und_Hoehenregler_RTBox_B_UZKJL2_8;
      if (Stromregler_und_Hoehenregler_RTBox_X_Spannung_OK && u < 17.)
      {
         Stromregler_und_Hoehenregler_RTBox_X_Spannung_OK = 0;
      }
      else if (!Stromregler_und_Hoehenregler_RTBox_X_Spannung_OK && u > 18.)
      {
         Stromregler_und_Hoehenregler_RTBox_X_Spannung_OK = 1;
      }
   }
   Stromregler_und_Hoehenregler_RTBox_B_Spannung_OK =
      (Stromregler_und_Hoehenregler_RTBox_X_Spannung_OK) ? 1. : 0.;

   /* Logical Operator : 'Stromregler_und_Hoehenregler_RTBox/Freigabe' */
   Stromregler_und_Hoehenregler_RTBox_B_Freigabe =
      Stromregler_und_Hoehenregler_RTBox_B_DigitalIn4 &&
      Stromregler_und_Hoehenregler_RTBox_B_Spannung_OK;

   /* Logical Operator : 'Stromregler_und_Hoehenregler_RTBox/Reset_PI' */
   Stromregler_und_Hoehenregler_RTBox_B_Reset_PI =
      !Stromregler_und_Hoehenregler_RTBox_B_Freigabe;

   /* Integrator : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1' */
   if (Stromregler_und_Hoehenregler_RTBox_X_Integrator1_i1_first ||
       (Stromregler_und_Hoehenregler_RTBox_B_Reset_PI != 0))
   {
      Stromregler_und_Hoehenregler_RTBox_X_Integrator1_x = 0.;
   }
   Stromregler_und_Hoehenregler_RTBox_B_Integrator1 =
      Stromregler_und_Hoehenregler_RTBox_X_Integrator1_x;

   /* Sum : 'Stromregler_und_Hoehenregler_RTBox/Sum'
    * incorporates
    *  Transfer Function : 'Stromregler_und_Hoehenregler_RTBox/I_Filter(fg=500)'
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/I_Offset'
    */
   Stromregler_und_Hoehenregler_RTBox_B_Sum =
      (3124.99999999999955*
       Stromregler_und_Hoehenregler_RTBox_X_I_Filter_fg_500_) -
      (-0.0120000000000000002);

   /* Sum : 'Stromregler_und_Hoehenregler_RTBox/Sum2'
    * incorporates
    *  Gain : 'Stromregler_und_Hoehenregler_RTBox/Gain'
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/Constant1'
    */
   Stromregler_und_Hoehenregler_RTBox_B_Sum2 =
      (-3.14999999999999991*
       Stromregler_und_Hoehenregler_RTBox_B_U_Laser) + 14.5;

   /* C-Script : 'Stromregler_und_Hoehenregler_RTBox/Ball_Detection' */
   Stromregler_und_Hoehenregler_RTBox_0_cScriptOutput(
                                                      &Stromregler_und_Hoehenregler_RTBox_cScriptStruct[
                                                         0]);
   if (*Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].errorStatus)
      Stromregler_und_Hoehenregler_RTBox_errorStatus =
         *Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].errorStatus;
   if (Stromregler_und_Hoehenregler_RTBox_subTaskHit[0])
   {
      /* C-Script : 'Stromregler_und_Hoehenregler_RTBox/Median_Hoehe' */
      Stromregler_und_Hoehenregler_RTBox_1_cScriptOutput(
                                                         &Stromregler_und_Hoehenregler_RTBox_cScriptStruct[
                                                            1]);
      if (*Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].errorStatus)
         Stromregler_und_Hoehenregler_RTBox_errorStatus =
            *Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].errorStatus;

      /* Sum : 'Stromregler_und_Hoehenregler_RTBox/Sum3'
       * incorporates
       *  Constant : 'Stromregler_und_Hoehenregler_RTBox/Hoehe_soll'
       */
      Stromregler_und_Hoehenregler_RTBox_B_Sum3 = 4. -
                                                  Stromregler_und_Hoehenregler_RTBox_B_Median_Hoehe;

      /* Discrete Transfer Function : 'Stromregler_und_Hoehenregler_RTBox/Hoehenregler_500Hz' */
      Stromregler_und_Hoehenregler_RTBox_B_Hoehenregler_500Hz =
         1.47812602509858371*
         (Stromregler_und_Hoehenregler_RTBox_B_Sum3 *
          Stromregler_und_Hoehenregler_RTBox_B_Ball_Detection)+
         0.126608265988284119*
         Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[0]-
         0.255753357921299163*
         Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[1]+
         0.12914636258536305*
         Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[2];

      /* Saturation : 'Stromregler_und_Hoehenregler_RTBox/Saturation1' */
      Stromregler_und_Hoehenregler_RTBox_B_Saturation1 =
         Stromregler_und_Hoehenregler_RTBox_B_Hoehenregler_500Hz;
      if (Stromregler_und_Hoehenregler_RTBox_B_Saturation1 > 10.)
      {
         Stromregler_und_Hoehenregler_RTBox_B_Saturation1 = 10.;
      }
      else if (Stromregler_und_Hoehenregler_RTBox_B_Saturation1 < -10.)
      {
         Stromregler_und_Hoehenregler_RTBox_B_Saturation1 = -10.;
      }

      /* Gain : 'Stromregler_und_Hoehenregler_RTBox/K_U_I' */
      Stromregler_und_Hoehenregler_RTBox_B_K_U_I =
         Stromregler_und_Hoehenregler_RTBox_P.K_U_I_K*
         Stromregler_und_Hoehenregler_RTBox_B_Saturation1;
   }
   /* Manual Signal Switch : 'Stromregler_und_Hoehenregler_RTBox/Manual Switch'
    * incorporates
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/I_Test'
    */
   Stromregler_und_Hoehenregler_RTBox_B_ManualSwitch =
      Stromregler_und_Hoehenregler_RTBox_P.ManualSwitch_SwitchState ? 0.5 :
      Stromregler_und_Hoehenregler_RTBox_B_K_U_I;

   /* Saturation : 'Stromregler_und_Hoehenregler_RTBox/I_Soll_Begrenzung' */
   Stromregler_und_Hoehenregler_RTBox_B_I_Soll_Begrenzung =
      Stromregler_und_Hoehenregler_RTBox_B_ManualSwitch;
   if (Stromregler_und_Hoehenregler_RTBox_B_I_Soll_Begrenzung > 5.)
   {
      Stromregler_und_Hoehenregler_RTBox_B_I_Soll_Begrenzung = 5.;
   }
   else if (Stromregler_und_Hoehenregler_RTBox_B_I_Soll_Begrenzung < 0.)
   {
      Stromregler_und_Hoehenregler_RTBox_B_I_Soll_Begrenzung = 0.;
   }

   /* Sum : 'Stromregler_und_Hoehenregler_RTBox/Subtract2' */
   Stromregler_und_Hoehenregler_RTBox_B_Subtract2 =
      Stromregler_und_Hoehenregler_RTBox_B_I_Soll_Begrenzung -
      Stromregler_und_Hoehenregler_RTBox_B_Sum;

   /* Sum : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Sum'
    * incorporates
    *  Product : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Product'
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Source Select/internal/Constant'
    *  Product : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Product3'
    *  Sum : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Sum1'
    *  Product : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Product2'
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Source Select/internal/Constant2'
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Kd Integrator/Kd = 0/Constant'
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Source Select/internal/Constant3'
    */
   Stromregler_und_Hoehenregler_RTBox_B_Sum_1 =
      (Stromregler_und_Hoehenregler_RTBox_B_Subtract2 *
       101.700000000000003) +
      (((Stromregler_und_Hoehenregler_RTBox_B_Subtract2 *
         0.) - 0.) * 0.) + Stromregler_und_Hoehenregler_RTBox_B_Integrator1;

   /* Saturation : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Saturation/internal/Saturation Select/constant/Saturation' */
   Stromregler_und_Hoehenregler_RTBox_B_Saturation =
      Stromregler_und_Hoehenregler_RTBox_B_Sum_1;
   if (Stromregler_und_Hoehenregler_RTBox_B_Saturation > 24.)
   {
      Stromregler_und_Hoehenregler_RTBox_B_Saturation = 24.;
   }
   else if (Stromregler_und_Hoehenregler_RTBox_B_Saturation < -24.)
   {
      Stromregler_und_Hoehenregler_RTBox_B_Saturation = -24.;
   }

   /* Product : 'Stromregler_und_Hoehenregler_RTBox/Product3' */
   Stromregler_und_Hoehenregler_RTBox_B_Product3 = 1. /
                                                   Stromregler_und_Hoehenregler_RTBox_B_UZK_Nenner
                                                   *
                                                   Stromregler_und_Hoehenregler_RTBox_B_Saturation;

   /* Relational Operator : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Relational\nOperator'
    * incorporates
    *  Product : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Product'
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Constant1'
    */
   Stromregler_und_Hoehenregler_RTBox_B_RelationalOperator =
      (Stromregler_und_Hoehenregler_RTBox_B_Sum_1 *
       Stromregler_und_Hoehenregler_RTBox_B_Subtract2) > 0.;

   /* Sum : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Sum' */
   Stromregler_und_Hoehenregler_RTBox_B_Sum_2 =
      -Stromregler_und_Hoehenregler_RTBox_B_Sum_1 +
      Stromregler_und_Hoehenregler_RTBox_B_Saturation;

   /* Sum : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Sum1'
    * incorporates
    *  Gain : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/rtol'
    *  Abs : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Abs4'
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/atol'
    */
   Stromregler_und_Hoehenregler_RTBox_B_Sum1 =
      (9.99999999999999955e-07*
       fabs(Stromregler_und_Hoehenregler_RTBox_B_Sum_1)) +
      2.22044604925031308e-14;

   /* Minimum / Maximum : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Dead Zone4/Min\/Max'
    * incorporates
    *  Zero-Order Hold : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Dead Zone4/Zero-Order\nHold1'
    */
   {
      double u, y;
      y = Stromregler_und_Hoehenregler_RTBox_B_Sum_2;
      u = Stromregler_und_Hoehenregler_RTBox_B_Sum1;
      if (u < y)
         y = u;
      Stromregler_und_Hoehenregler_RTBox_B_Min_Max = y;
   }

   /* Minimum / Maximum : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Dead Zone4/Min\/Max1'
    * incorporates
    *  Gain : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Dead Zone4/Gain'
    */
   {
      double u, y;
      y = Stromregler_und_Hoehenregler_RTBox_B_Min_Max;
      u = -1.*Stromregler_und_Hoehenregler_RTBox_B_Sum1;
      if (u > y)
         y = u;
      Stromregler_und_Hoehenregler_RTBox_B_Min_Max1 = y;
   }
   /* Digital Out : 'Stromregler_und_Hoehenregler_RTBox/Enable1' */
   writeDigitalOut(12, Stromregler_und_Hoehenregler_RTBox_B_Freigabe);
   writeDigitalOut(13, Stromregler_und_Hoehenregler_RTBox_B_Freigabe);
   writeDigitalOut(14, Stromregler_und_Hoehenregler_RTBox_B_Freigabe);
   /* Saturation : 'Stromregler_und_Hoehenregler_RTBox/Saturation' */
   Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[0] =
      Stromregler_und_Hoehenregler_RTBox_B_Product3;
   if (Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[0] >
       0.900000000000000022)
   {
      Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[0] =
         0.900000000000000022;
   }
   else if (Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[0] <
            -0.900000000000000022)
   {
      Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[0] =
         -0.900000000000000022;
   }
   Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[1] =
      Stromregler_und_Hoehenregler_RTBox_B_Product3;
   if (Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[1] >
       0.900000000000000022)
   {
      Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[1] =
         0.900000000000000022;
   }
   else if (Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[1] <
            -0.900000000000000022)
   {
      Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[1] =
         -0.900000000000000022;
   }
   Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[2] =
      Stromregler_und_Hoehenregler_RTBox_B_Product3;
   if (Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[2] >
       0.900000000000000022)
   {
      Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[2] =
         0.900000000000000022;
   }
   else if (Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[2] <
            -0.900000000000000022)
   {
      Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[2] =
         -0.900000000000000022;
   }
   Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[3] =
      Stromregler_und_Hoehenregler_RTBox_B_Product3;
   if (Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[3] >
       0.900000000000000022)
   {
      Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[3] =
         0.900000000000000022;
   }
   else if (Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[3] <
            -0.900000000000000022)
   {
      Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[3] =
         -0.900000000000000022;
   }

   /* PWM Out : 'Stromregler_und_Hoehenregler_RTBox/S J2' */
   {
      const int periodPWM_int = 1334;
      const float gain = 6.667500000e+02f;
      {
         int cmpPWM =
            (int)(((Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[0]) +
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
            (int)(((Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[1]) +
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
            (int)(((Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[2]) +
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
            (int)(((Stromregler_und_Hoehenregler_RTBox_B_Saturation_1[3]) +
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
   Stromregler_und_Hoehenregler_RTBox_ExtModeBuffer[0] =
      (double)Stromregler_und_Hoehenregler_RTBox_B_Freigabe;
   Stromregler_und_Hoehenregler_RTBox_ExtModeBuffer[1] =
      (double)Stromregler_und_Hoehenregler_RTBox_B_DigitalIn4;
#endif /* defined(EXTERNAL_MODE) */

   if (Stromregler_und_Hoehenregler_RTBox_errorStatus)
   {
      return;
   }

   /* Update for Integrator : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1' */
   Stromregler_und_Hoehenregler_RTBox_X_Integrator1_i1_first = 0;

   /* Update for C-Script : 'Stromregler_und_Hoehenregler_RTBox/Ball_Detection' */
   Stromregler_und_Hoehenregler_RTBox_0_cScriptUpdate(
                                                      &Stromregler_und_Hoehenregler_RTBox_cScriptStruct[
                                                         0]);
   if (*Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].errorStatus)
      Stromregler_und_Hoehenregler_RTBox_errorStatus =
         *Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].errorStatus;
   if (Stromregler_und_Hoehenregler_RTBox_subTaskHit[0])
   {
      /* Update for C-Script : 'Stromregler_und_Hoehenregler_RTBox/Median_Hoehe' */
      Stromregler_und_Hoehenregler_RTBox_1_cScriptUpdate(
                                                         &Stromregler_und_Hoehenregler_RTBox_cScriptStruct[
                                                            1]);
      if (*Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].errorStatus)
         Stromregler_und_Hoehenregler_RTBox_errorStatus =
            *Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].errorStatus;

      /* Update for Discrete Transfer Function : 'Stromregler_und_Hoehenregler_RTBox/Hoehenregler_500Hz'
       * incorporates
       *  Product : 'Stromregler_und_Hoehenregler_RTBox/Product'
       */
      {
         double newX;
         newX =
            (Stromregler_und_Hoehenregler_RTBox_B_Sum3 *
             Stromregler_und_Hoehenregler_RTBox_B_Ball_Detection)+
            0.963729995961989605*
            Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[0]-
            2.92706352213247456*
            Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[1]+
            2.96333216700081925*
            Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[2];
         Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[0] =
            Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[1];
         Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[1] =
            Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[2];
         Stromregler_und_Hoehenregler_RTBox_X_Hoehenregler_500Hz[2] = newX;
      }
   }

   /* Increment sub-task tick counters */
   {
      size_t i;
      for (i = 0; i < 1; ++i)
      {
         Stromregler_und_Hoehenregler_RTBox_subTaskTick[i]++;
         if (Stromregler_und_Hoehenregler_RTBox_subTaskTick[i] >=
             Stromregler_und_Hoehenregler_RTBox_subTaskPeriod[i])
         {
            Stromregler_und_Hoehenregler_RTBox_subTaskTick[i] = 0;
         }
      }
   }

   /* Derivatives for Integrator : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Ki Integrator/Ki ~= 0/Integrator/level_triggered/Integrator1'
    * incorporates
    *  Sum : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Sum3'
    *  Product : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Continous Time/Product1'
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Source Select/internal/Constant1'
    *  Logical Operator : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Logical\nOperator2'
    *  Logical Operator : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Logical\nOperator1'
    *  Sum : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Dead Zone4/Sum2'
    *  Constant : 'Stromregler_und_Hoehenregler_RTBox/Continuous PID\nController3/Anti-windup\nmethod/Conditional Integration/Constant'
    */
   if (Stromregler_und_Hoehenregler_RTBox_B_Reset_PI != 0)
   {
      Stromregler_und_Hoehenregler_RTBox_deriv[0] = 0;
   }
   else
   {
      Stromregler_und_Hoehenregler_RTBox_deriv[0] =
         (Stromregler_und_Hoehenregler_RTBox_B_Subtract2 *
          816.799999999999955 *
          ((double)(!(Stromregler_und_Hoehenregler_RTBox_B_RelationalOperator
                      &&
                      (-Stromregler_und_Hoehenregler_RTBox_B_Min_Max1 +
                       Stromregler_und_Hoehenregler_RTBox_B_Sum_2))))) + 0.;
   }

   /* Derivatives for Transfer Function : 'Stromregler_und_Hoehenregler_RTBox/I_Filter(fg=500)'
    * incorporates
    *  Sum : 'Stromregler_und_Hoehenregler_RTBox/Sum1'
    */
   Stromregler_und_Hoehenregler_RTBox_deriv[1] =
      (Stromregler_und_Hoehenregler_RTBox_B_IABJL2_16 +
       Stromregler_und_Hoehenregler_RTBox_B_ICDJL2_14)-3124.99999999999955*
      Stromregler_und_Hoehenregler_RTBox_X_I_Filter_fg_500_;

   /* Update continuous states */
   Stromregler_und_Hoehenregler_RTBox_X_Integrator1_x +=
      2.00000000000000016e-05*Stromregler_und_Hoehenregler_RTBox_deriv[0];
   Stromregler_und_Hoehenregler_RTBox_X_I_Filter_fg_500_ +=
      2.00000000000000016e-05*Stromregler_und_Hoehenregler_RTBox_deriv[1];
}

void Stromregler_und_Hoehenregler_RTBox_terminate(void)
{
   /* Termination for C-Script : 'Stromregler_und_Hoehenregler_RTBox/Ball_Detection' */
   Stromregler_und_Hoehenregler_RTBox_0_cScriptTerminate(
                                                         &Stromregler_und_Hoehenregler_RTBox_cScriptStruct[
                                                            0]);
   if (*Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].errorStatus)
      Stromregler_und_Hoehenregler_RTBox_errorStatus =
         *Stromregler_und_Hoehenregler_RTBox_cScriptStruct[0].errorStatus;
   /* Termination for C-Script : 'Stromregler_und_Hoehenregler_RTBox/Median_Hoehe' */
   Stromregler_und_Hoehenregler_RTBox_1_cScriptTerminate(
                                                         &Stromregler_und_Hoehenregler_RTBox_cScriptStruct[
                                                            1]);
   if (*Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].errorStatus)
      Stromregler_und_Hoehenregler_RTBox_errorStatus =
         *Stromregler_und_Hoehenregler_RTBox_cScriptStruct[1].errorStatus;
}
