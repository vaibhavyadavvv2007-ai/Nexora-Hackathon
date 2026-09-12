"use client";

import { useState, useCallback } from "react";
import { EvaluationResult, ProcessingStatus, CandidateEvaluation, PairwiseComparison } from "@/types";
import {
  submitEvaluation,
  getCandidateDetail,
  getPairwiseComparison,
} from "@/services/api";
import { getMockProcessingStatus } from "@/data/mock-data";

export function useEvaluation() {
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [status, setStatus] = useState<ProcessingStatus>(getMockProcessingStatus("idle"));
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runEvaluation = useCallback(async (jdFile: File | null, resumeFiles: File[]) => {
    setIsProcessing(true);
    setError(null);

    try {
      // Simulate processing stages
      const stages: ProcessingStatus["stage"][] = ["uploading", "parsing", "matching", "ranking", "complete"];
      for (const stage of stages) {
        setStatus(getMockProcessingStatus(stage));
        await new Promise((r) => setTimeout(r, 600));
      }

      const evalResult = await submitEvaluation(jdFile, resumeFiles);
      setResult(evalResult);
      setStatus(getMockProcessingStatus("complete"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
      setStatus(getMockProcessingStatus("error"));
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setStatus(getMockProcessingStatus("idle"));
    setIsProcessing(false);
    setError(null);
  }, []);

  return { result, status, isProcessing, error, runEvaluation, reset };
}

export function useCandidateDetail() {
  const [candidate, setCandidate] = useState<CandidateEvaluation | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadCandidate = useCallback(async (id: string) => {
    setIsLoading(true);
    const data = await getCandidateDetail(id);
    setCandidate(data);
    setIsLoading(false);
  }, []);

  return { candidate, isLoading, loadCandidate };
}

export function useComparison() {
  const [comparison, setComparison] = useState<PairwiseComparison | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const compare = useCallback(async (aId: string, bId: string) => {
    setIsLoading(true);
    const data = await getPairwiseComparison(aId, bId);
    setComparison(data);
    setIsLoading(false);
  }, []);

  const clearComparison = useCallback(() => {
    setComparison(null);
  }, []);

  return { comparison, isLoading, compare, clearComparison };
}
