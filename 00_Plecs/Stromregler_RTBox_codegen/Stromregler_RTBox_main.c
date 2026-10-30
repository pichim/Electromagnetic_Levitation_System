#include "plexim/HIL_Framework.h"
#include "plexim/ScopeBuffer.h"
#include "plexim/DigitalOut.h"
#include "plexim/DigitalOverride.h"
#include "plexim/Encoder.h"
#include "plexim/SPI.h"
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdatomic.h>
#include "Stromregler_RTBox.h"

#define MODEL_PREFIX Stromregler_RTBox
#define MODEL_NAME "Stromregler_RTBox"
#define CONCAT_(a, b) a ## b
#define CONCAT(a, b) CONCAT_(a, b)
#define MODEL_FLOAT_TYPE CONCAT(MODEL_PREFIX, _FloatType)
#define MODEL_SAMPLE_TIME CONCAT(MODEL_PREFIX, _sampleTime)
#define MODEL_STEP CONCAT(MODEL_PREFIX, _step)
#define MODEL_ERROR_STATUS CONCAT(MODEL_PREFIX, _errorStatus)
#define MODEL_CHECKSUM CONCAT(MODEL_PREFIX, _checksum)
#define MODEL_INITIALIZE CONCAT(MODEL_PREFIX, _initialize)
#define MODEL_TERMINATE CONCAT(MODEL_PREFIX, _terminate)

#define min(a, b) ((a) < (b)) ? (a) : (b)
#define likely(x)       __builtin_expect((x),1)
#define unlikely(x)     __builtin_expect((x),0)
#define plxMulticoreSyncedStep()

#define MULTITASKING 0

#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
#define MODEL_NUM_EXT_MODE_SIGNALS CONCAT(MODEL_PREFIX, _NumExtModeSignals)
#define MODEL_EXT_MODE_SIGNALS CONCAT(MODEL_PREFIX, _ExtModeSignals)
#define MODEL_NUM_TUNABLE_PARAMETERS CONCAT(MODEL_PREFIX, _NumTunableParameters)
#define MODEL_TUNABLE_PARAMETERS CONCAT(MODEL_PREFIX, _P)

#pragma pack(push, 4)

struct ArmResponse
{
   int msg;
   int mMsgLength;
   int mTransactionId;
   int mLength;
   float mSampleTime;
   int mBufferIndex;
   int mOffset;
   int mNumActiveSignals;
   unsigned short mActiveSignals[MODEL_NUM_EXT_MODE_SIGNALS];
};

struct TriggerInfo
{
   int mTransactionId;
   int mLength;
   int mEdge; 
   float mTriggerValue;
   int mTriggerChannel;
   int mDecimation;
   int mTriggerDelay;
   int mNumActiveSignals;
   unsigned short mActiveSignals[MODEL_NUM_EXT_MODE_SIGNALS];
   const MODEL_FLOAT_TYPE* mTriggerChannelValue;
   const MODEL_FLOAT_TYPE* mActiveSignalValues[MODEL_NUM_EXT_MODE_SIGNALS];
};

#pragma pack(pop)

static struct TriggerInfo mTriggerInfo;

static void initializeScopeTrigger(void)
{
#if MODEL_NUM_EXT_MODE_SIGNALS
   if (mTriggerInfo.mTriggerChannel >= 0)
      mTriggerInfo.mTriggerChannelValue = MODEL_EXT_MODE_SIGNALS[mTriggerInfo.mTriggerChannel];
   else
      mTriggerInfo.mTriggerChannelValue = MODEL_EXT_MODE_SIGNALS[0];
   int i=0;
   for (i=0; i<mTriggerInfo.mNumActiveSignals; i++)
   {
      int signalIdx = min(mTriggerInfo.mActiveSignals[i], MODEL_NUM_EXT_MODE_SIGNALS-1);
      mTriggerInfo.mActiveSignalValues[i] = MODEL_EXT_MODE_SIGNALS[signalIdx];
   }
#endif /* MODEL_NUM_EXT_MODE_SIGNALS */
}

static void checkScopeTrigger(void)
{
   static float lastTriggerSignal = 0;
   static int decimationCounter = 1;

   if (scopeArmed)
   {
      float triggerSignal = *mTriggerInfo.mTriggerChannelValue;
      decimationCounter--;
      if (!decimationCounter)
      {
         struct ScopeBuffer* currentBufferPtr = &plxScopeBuffer[plxCurrentWriteBuffer];
         int i=0;
         for (; i < mTriggerInfo.mNumActiveSignals; i++)
         {
            addToScopeBuffer(currentBufferPtr, *mTriggerInfo.mActiveSignalValues[i]);
         }
         if (!scopeTriggered && getScopeBufferNumValidElements(currentBufferPtr) * mTriggerInfo.mDecimation > -mTriggerInfo.mTriggerDelay * mTriggerInfo.mNumActiveSignals )
         {
            if (mTriggerInfo.mEdge == 0 && lastTriggerSignal < mTriggerInfo.mTriggerValue && triggerSignal >= mTriggerInfo.mTriggerValue) scopeTriggered = TRUE;
            else if (mTriggerInfo.mEdge == 1 && lastTriggerSignal > mTriggerInfo.mTriggerValue && triggerSignal <= mTriggerInfo.mTriggerValue) scopeTriggered = TRUE;
            if (scopeTriggered)
               setScopeBufferNumValidElements(currentBufferPtr, (-mTriggerInfo.mTriggerDelay / mTriggerInfo.mDecimation + 1) * mTriggerInfo.mNumActiveSignals);
         }
         lastTriggerSignal = triggerSignal;
         if (scopeTriggered)
         {
            if (getScopeBufferNumValidElements(currentBufferPtr) >= getScopeBufferSize(currentBufferPtr))
            {
               scopeArmed = FALSE;
               setScopeBufferFull(currentBufferPtr, TRUE);
               scopeTriggered = FALSE;
               plxCurrentWriteBuffer = !plxCurrentWriteBuffer;
            }
         }
         decimationCounter = mTriggerInfo.mDecimation;
      }
   }
   else
   {
      lastTriggerSignal = NAN;
   }
}

static void copyTunableParameters(const double* aData)
{
  MODEL_TUNABLE_PARAMETERS.K_U_I_K = (double)*aData++;
}

#else
static void initializeScopeTrigger(void) {}
static void copyTunableParameters(const double* aData) { (void)aData; }
#define checkScopeTrigger()
#endif /* defined(EXTERNAL_MODE) */

struct PlxNanostepSignal plxNanostepSignals[] = {
};

uint32_t plxActiveTasks = 1;

int plxPlatform_poll(void);
static void modelInitFunction(void)
{
   MODEL_INITIALIZE(0);
   postInitCode();
   // Run step functions a few times to have code in cache
   for (int i=0; i<10; i++)
   {
      if (!plxErrorFlag)
      {
         MODEL_STEP();
         plxPlatform_poll();
      }
   }
   if (!plxErrorFlag)
   {
      MODEL_TERMINATE();
   }
   plxPreparePwmUpdate(0xf0000);
   MODEL_INITIALIZE(0);
   postInitCode();
}


void plxGeneratedMultiCorePreStepFunction(bool aCore2AboutToStart, bool aCore3AboutToStart)
{
   plxUpdatePWMCycleRate();
   {
      PLX_BOOL sfpInitialized = FALSE;
      if (!sfpInitialized) sfpInitialized = plxCheckSFPInitialization();
   }
   (void)aCore2AboutToStart;
   (void)aCore3AboutToStart;
}

void plxGeneratedSingleCorePreStepFunction(void)
{
   plxUpdatePWMCycleRate();
   {
      PLX_BOOL sfpInitialized = FALSE;
      if (!sfpInitialized) sfpInitialized = plxCheckSFPInitialization();
   }
}

void modelStepFunction0(void)
{
   /* Execute base task. */
   MODEL_STEP();
   if(unlikely((size_t)MODEL_ERROR_STATUS))
   {
      plxStopTimer();
      const char* assertionDetails = plxGetSavedAssertionDetails();
      if (assertionDetails)
      {
         plxUserMessage(PLXUSERMSG_NEEDS_ATTENTION, "%s Assertion was caused by "
         "digital inputs %s.\n", MODEL_ERROR_STATUS, assertionDetails);
      }
      else
      {
         plxUserMessage(PLXUSERMSG_NEEDS_ATTENTION, "%s\n", MODEL_ERROR_STATUS);
      }
      plxErrorFlag = 1;

      plxWaitForIrqAck();

   }
   if (unlikely(plxErrorFlag))
      return;
   
#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
   checkScopeTrigger();
#endif /* defined(EXTERNAL_MODE) */

   plxSyncDigitalOuts();
   plxToggleDmaFlag();
   plxPostBaseStep();
}

void modelStepFunction1(void)
{
}

void modelStepFunction2(void)
{
}

int main(void)
{
   int useExternalMode = 0;
   int numExtModeSignals = 0;
   void* tunableParameterValues = NULL;
   int numTunableParameters = 0;
   struct PlxTriggerInfo* trigger = NULL;
   struct PlxArmResponse* armResponse = NULL;
   struct PlxModelFunctions modelFunctions = 
   {
      .init = &modelInitFunction,
      .step = &modelStepFunction0,
      .terminate = &MODEL_TERMINATE,
      .initializeScopeTrigger = &initializeScopeTrigger,
      .copyTunableParams = &copyTunableParameters
   };
#if defined(EXTERNAL_MODE) && EXTERNAL_MODE
   useExternalMode = 1;
   numExtModeSignals = MODEL_NUM_EXT_MODE_SIGNALS;
   memset((void*)&mTriggerInfo, 0, sizeof(struct PlxTriggerInfo));
   trigger = (struct PlxTriggerInfo*)&mTriggerInfo;
   static struct ArmResponse armResponseInst;
   armResponse = (struct PlxArmResponse*)&armResponseInst;
#if (MODEL_NUM_TUNABLE_PARAMETERS > 0)
   numTunableParameters = MODEL_NUM_TUNABLE_PARAMETERS;
   tunableParameterValues = &MODEL_TUNABLE_PARAMETERS;
#endif
#endif
   plxRegisterBackgroundTask(plxStandaloneBackgroundTask);
#if defined(MULTITASKING) && MULTITASKING
   double sampleTime = MODEL_SAMPLE_TIME[0][0];
#else
   double sampleTime = MODEL_SAMPLE_TIME;
#endif
   plxStartSimulationModel(sampleTime, sizeof(MODEL_FLOAT_TYPE),
                           useExternalMode, numExtModeSignals,
                           0, numTunableParameters,
                           trigger, armResponse, MODEL_CHECKSUM, MODEL_NAME,
                           &modelFunctions,  plxNanostepSignals,
                           1, 1, 
                           1);
}
