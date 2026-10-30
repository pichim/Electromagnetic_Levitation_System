/*
 * Header file for: Stromregler_RTBox
 * Generated with : PLECS 5.0.6
 *                  PLECS RT Box 1 4.0.8
 * Generated on   : 29 Oct 2026 15:39:47
 */
#ifndef PLECS_HEADER_Stromregler_RTBox_h_
#define PLECS_HEADER_Stromregler_RTBox_h_

#include <stdbool.h>
#include <stdint.h>

/* Model floating point type */
typedef double Stromregler_RTBox_FloatType;

/* Model checksum */
extern const char * const Stromregler_RTBox_checksum;

/* Model error status */
extern const char * Stromregler_RTBox_errorStatus;


/* Model sample time */
extern const double Stromregler_RTBox_sampleTime;


#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
/* External mode signals */
#define Stromregler_RTBox_NumExtModeSignals 20
extern const double * const Stromregler_RTBox_ExtModeSignals[];
/* Tunable parameters */
#define Stromregler_RTBox_NumTunableParameters 1
#endif /* defined(EXTERNAL_MODE) */


/* Block parameters */
typedef struct
{
   /* Parameter 'K' of
    *  Gain : 'Stromregler_RTBox/K_U_I'
    */
   double K_U_I_K;
} Stromregler_RTBox_Parameters;
extern Stromregler_RTBox_Parameters Stromregler_RTBox_P;

/* Entry point functions */
void Stromregler_RTBox_initialize(double time);
void Stromregler_RTBox_step(void);
void Stromregler_RTBox_terminate(void);

#endif /* PLECS_HEADER_Stromregler_RTBox_h_ */
