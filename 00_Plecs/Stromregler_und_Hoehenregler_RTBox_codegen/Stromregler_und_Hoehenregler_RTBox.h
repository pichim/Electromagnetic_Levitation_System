/*
 * Header file for: Stromregler_und_Hoehenregler_RTBox
 * Generated with : PLECS 5.0.6
 *                  PLECS RT Box 1 4.0.8
 * Generated on   : 5 Nov 2026 16:58:06
 */
#ifndef PLECS_HEADER_Stromregler_und_Hoehenregler_RTBox_h_
#define PLECS_HEADER_Stromregler_und_Hoehenregler_RTBox_h_

#include <stdbool.h>
#include <stdint.h>

/* Model floating point type */
typedef double Stromregler_und_Hoehenregler_RTBox_FloatType;

/* Model checksum */
extern const char * const Stromregler_und_Hoehenregler_RTBox_checksum;

/* Model error status */
extern const char * Stromregler_und_Hoehenregler_RTBox_errorStatus;


/* Model sample time */
extern const double Stromregler_und_Hoehenregler_RTBox_sampleTime;


#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
/* External mode signals */
#define Stromregler_und_Hoehenregler_RTBox_NumExtModeSignals 30
extern const double * const Stromregler_und_Hoehenregler_RTBox_ExtModeSignals
[];
/* Tunable parameters */
#define Stromregler_und_Hoehenregler_RTBox_NumTunableParameters 2
#endif /* defined(EXTERNAL_MODE) */


/* Block parameters */
typedef struct
{
   /* Parameter 'K' of
    *  Gain : 'Stromregler_und_Hoehenregler_RTBox/K_U_I'
    */
   double K_U_I_K;
   /* Parameter 'SwitchState' of
    *  Manual Signal Switch : 'Stromregler_und_Hoehenregler_RTBox/Manual Switch'
    */
   bool ManualSwitch_SwitchState;
} Stromregler_und_Hoehenregler_RTBox_Parameters;
extern Stromregler_und_Hoehenregler_RTBox_Parameters
   Stromregler_und_Hoehenregler_RTBox_P;

/* Entry point functions */
void Stromregler_und_Hoehenregler_RTBox_initialize(double time);
void Stromregler_und_Hoehenregler_RTBox_step(void);
void Stromregler_und_Hoehenregler_RTBox_terminate(void);

#endif /* PLECS_HEADER_Stromregler_und_Hoehenregler_RTBox_h_ */
