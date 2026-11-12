/*
 * Header file for: Chirp_Messung_Spule
 * Generated with : PLECS 5.0.6
 *                  PLECS RT Box 1 4.0.8
 * Generated on   : 11 Nov 2026 10:19:55
 */
#ifndef PLECS_HEADER_Chirp_Messung_Spule_h_
#define PLECS_HEADER_Chirp_Messung_Spule_h_

#include <stdbool.h>
#include <stdint.h>

/* Model floating point type */
typedef double Chirp_Messung_Spule_FloatType;

/* Model checksum */
extern const char * const Chirp_Messung_Spule_checksum;

/* Model error status */
extern const char * Chirp_Messung_Spule_errorStatus;


/* Model sample time */
extern const double Chirp_Messung_Spule_sampleTime;


#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
/* External mode signals */
#define Chirp_Messung_Spule_NumExtModeSignals 20
extern const double * const Chirp_Messung_Spule_ExtModeSignals[];
/* Tunable parameters */
#define Chirp_Messung_Spule_NumTunableParameters 1
#endif /* defined(EXTERNAL_MODE) */


/* Block parameters */
typedef struct
{
   /* Parameter 'SwitchState' of
    *  Manual Signal Switch : 'Chirp_Messung_Spule/Manual Switch1'
    */
   bool ManualSwitch1_SwitchState;
} Chirp_Messung_Spule_Parameters;
extern Chirp_Messung_Spule_Parameters Chirp_Messung_Spule_P;

/* Entry point functions */
void Chirp_Messung_Spule_initialize(double time);
void Chirp_Messung_Spule_step(void);
void Chirp_Messung_Spule_terminate(void);

#endif /* PLECS_HEADER_Chirp_Messung_Spule_h_ */
