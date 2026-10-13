import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { WeldAnalysisRequest, WeldAnalysisResponse } from '../types/weld'

interface WeldAnalysisContextValue {
  lastInputs: WeldAnalysisRequest | null
  lastResult: WeldAnalysisResponse | null
  setLastAnalysis: (inputs: WeldAnalysisRequest, result: WeldAnalysisResponse) => void
}

const WeldAnalysisContext = createContext<WeldAnalysisContextValue>({
  lastInputs: null,
  lastResult: null,
  setLastAnalysis: () => {},
})

export function WeldAnalysisProvider({ children }: { children: ReactNode }) {
  const [lastInputs, setLastInputs] = useState<WeldAnalysisRequest | null>(null)
  const [lastResult, setLastResult] = useState<WeldAnalysisResponse | null>(null)

  function setLastAnalysis(inputs: WeldAnalysisRequest, result: WeldAnalysisResponse) {
    setLastInputs(inputs)
    setLastResult(result)
  }

  return (
    <WeldAnalysisContext.Provider value={{ lastInputs, lastResult, setLastAnalysis }}>
      {children}
    </WeldAnalysisContext.Provider>
  )
}

export function useWeldAnalysis() {
  return useContext(WeldAnalysisContext)
}
