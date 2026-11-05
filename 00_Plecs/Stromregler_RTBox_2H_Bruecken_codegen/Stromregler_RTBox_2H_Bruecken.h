/*
 * Header file for: Stromregler_RTBox_2H_Bruecken
 * Generated with : PLECS 5.0.6
 *                  PLECS RT Box 1 4.0.8
 * Generated on   : 5 Nov 2026 14:32:45
 */
#ifndef PLECS_HEADER_Stromregler_RTBox_2H_Bruecken_h_
#define PLECS_HEADER_Stromregler_RTBox_2H_Bruecken_h_

#include <stdbool.h>
#include <stdint.h>

/* Model floating point type */
typedef double Stromregler_RTBox_2H_Bruecken_FloatType;

/* Model checksum */
extern const char * const Stromregler_RTBox_2H_Bruecken_checksum;

/* Model error status */
extern const char * Stromregler_RTBox_2H_Bruecken_errorStatus;


/* Model sample time */
extern const double Stromregler_RTBox_2H_Bruecken_sampleTime;


#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
/* External mode signals */
#define Stromregler_RTBox_2H_Bruecken_NumExtModeSignals 31
extern const double * const Stromregler_RTBox_2H_Bruecken_ExtModeSignals[];
/* Tunable parameters */
#define Stromregler_RTBox_2H_Bruecken_NumTunableParameters 3
#endif /* defined(EXTERNAL_MODE) */


/* Block parameters */
typedef struct
{
   /* Parameter 'K' of
    *  Gain : 'Stromregler_RTBox_2H_Bruecken/K_U_I'
    */
   double K_U_I_K;
   /* Parameter 'SwitchState' of
    *  Manual Signal Switch : 'Stromregler_RTBox_2H_Bruecken/Manual Switch'
    */
   double ManualSwitch_SwitchState;
   /* Parameter 'SwitchState' of
    *  Manual Signal Switch : 'Stromregler_RTBox_2H_Bruecken/Manual Switch1'
    */
   bool ManualSwitch1_SwitchState;
} Stromregler_RTBox_2H_Bruecken_Parameters;
extern Stromregler_RTBox_2H_Bruecken_Parameters
   Stromregler_RTBox_2H_Bruecken_P;

/* Entry point functions */
void Stromregler_RTBox_2H_Bruecken_initialize(double time);
void Stromregler_RTBox_2H_Bruecken_step(void);
void Stromregler_RTBox_2H_Bruecken_terminate(void);

#endif /* PLECS_HEADER_Stromregler_RTBox_2H_Bruecken_h_ */
