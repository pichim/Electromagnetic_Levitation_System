/*
 * C-Script file for: Stromregler_und_Hoehenregler_RTBox/Ball_Detection
 * Generated with   : PLECS 5.0.6
 * Generated on     : 5 Nov 2026 16:58:06
 */
typedef double real_t;
#define REAL_MAX DBL_MAX
#define REAL_MIN DBL_MIN
#define REAL_EPSILON DBL_EPSILON

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
#define NumInputs cScriptStruct->numInputSignals[0]
#define NumOutputs cScriptStruct->numOutputSignals[0]
#define Input(signalIdx) (*cScriptStruct->inputs[0][signalIdx])
#define Output(signalIdx) (*cScriptStruct->outputs[0][signalIdx])
#define NumInputTerminals cScriptStruct->numInputTerminals
#define NumOutputTerminals cScriptStruct->numOutputTerminals
#define NumInputSignals(terminalIdx) cScriptStruct->numInputSignals[ \
      terminalIdx]
#define NumOutputSignals(terminalIdx) cScriptStruct->numOutputSignals[ \
      terminalIdx]
#define InputSignal(terminalIdx, \
                    signalIdx) (*cScriptStruct->inputs[terminalIdx][signalIdx])
#define OutputSignal(terminalIdx, \
                     signalIdx) (*cScriptStruct->outputs[terminalIdx][ \
                                    signalIdx])
#define NumContStates cScriptStruct->numContStates
#define NumDiscStates cScriptStruct->numDiscStates
#define NumZCSignals cScriptStruct->numZCSignals
#define NumParameters cScriptStruct->numParameters
#define NumSampleTimes cScriptStruct->numSampleTimes
#define IsMajorStep cScriptStruct->isMajorTimeStep
#define IsRefineStep cScriptStruct->isRefineStep
#define CurrentTime cScriptStruct->time
#define NextSampleHit (*cScriptStruct->nextSampleHit)
#define SetErrorMessage(string) { *cScriptStruct->errorStatus=(string); }
#define SetWarningMessage(string)
#define ContState(idx) cScriptStruct->contStates[idx]
#define ContDeriv(idx) cScriptStruct->contDerivs[idx]
#define DiscState(idx) cScriptStruct->discStates[idx]
#define ZCSignal(idx) cScriptStruct->zCSignals[idx]
#define IsSampleHit(idx) (*cScriptStruct->sampleHits[idx])
#define SampleTimePeriod(idx) cScriptStruct->sampleTimePeriods[idx]
#define SampleTimeOffset(idx) cScriptStruct->sampleTimeOffsets[idx]
#define InputSampleTimePeriod(terminalIdx, \
                              signalIdx) cScriptStruct->inputSampleTimePeriods \
   [terminalIdx][signalIdx]
#define InputSampleTimeOffset(terminalIdx, \
                              signalIdx) cScriptStruct->inputSampleTimeOffsets \
   [terminalIdx][signalIdx]
#define ParamNumDims(idx) cScriptStruct->paramNumDims[idx]
#define ParamDim(pIdx, dIdx) cScriptStruct->paramDims[pIdx][dIdx]
#define ParamRealData(pIdx, dIdx) cScriptStruct->paramRealData[pIdx][dIdx]
#define ParamStringData(pIdx) cScriptStruct->paramStringData[pIdx]

void Stromregler_und_Hoehenregler_RTBox_0_cScriptStart(
                                                       const struct CScriptStruct *cScriptStruct)
{
   DiscState(0) = -1.0; /* Zustand beim ersten Aufruf bestimmen */
   DiscState(1) = 0.0; /* Anzahl Schritte im neuen Zustand */
}

void Stromregler_und_Hoehenregler_RTBox_0_cScriptOutput(
                                                        const struct CScriptStruct *cScriptStruct)
{
   double neu = (InputSignal(0, 0) >= -1.0) ? 1.0 : 0.0;
   double alt = DiscState(0);

   if (alt < 0.0 ||
       (neu != alt && DiscState(1) + 1.0 >= ParamRealData(0, 0)))
      OutputSignal(0, 0) = neu;
   else
      OutputSignal(0, 0) = alt;
}

void Stromregler_und_Hoehenregler_RTBox_0_cScriptUpdate(
                                                        const struct CScriptStruct *cScriptStruct)
{
   double neu = (InputSignal(0, 0) >= -1.0) ? 1.0 : 0.0;

   if (DiscState(0) < 0.0)
   {
      DiscState(0) = neu;
      DiscState(1) = 0.0;
   }
   else if (neu == DiscState(0))
   {
      DiscState(1) = 0.0;
   }
   else
   {
      DiscState(1) += 1.0;

      if (DiscState(1) >= ParamRealData(0, 0))
      {
         DiscState(0) = neu;
         DiscState(1) = 0.0;
      }
   }
}

void Stromregler_und_Hoehenregler_RTBox_0_cScriptDerivative(
                                                            const struct CScriptStruct *cScriptStruct)
{
}

void Stromregler_und_Hoehenregler_RTBox_0_cScriptTerminate(
                                                           const struct CScriptStruct *cScriptStruct)
{
}
