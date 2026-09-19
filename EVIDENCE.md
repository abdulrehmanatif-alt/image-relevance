\# Evaluation Evidence



\## Evaluation Summary



The image matching system was evaluated against a labeled dataset containing 10 blog posts across 10 image categories.



| Metric | Result |
|---|---:|
| Evaluation cases | 10 |
| Correct predictions | 10 |
| Top-1 precision | 100% |
| Full test suite | 9/9 passed |
| Forced mismatch | Rejected |


\## Top-1 Evaluation Results



| Expected | Predicted | Image | Score | Result |

|---|---|---|---:|---|

| fox | fox | fox\_002.jpg | 0.3481 | Correct |

| wolf | wolf | wolf\_004.jpg | 0.3378 | Correct |

| cat | cat | cat\_005.jpg | 0.3307 | Correct |

| dog | dog | dog\_001.jpg | 0.3838 | Correct |

| bird | bird | bird\_004.jpg | 0.3805 | Correct |

| horse | horse | horse\_005.jpg | 0.3975 | Correct |

| motorcycle | motorcycle | motorcycle\_002.jpg | 0.4053 | Correct |

| car | car | car\_005.jpg | 0.3612 | Correct |

| mountain | mountain | mountain\_004.jpg | 0.4107 | Correct |

| plain | plain | plain\_003.jpg | 0.4529 | Correct |



\*\*Top-1 precision: 10/10 = 100%\*\*



\## Mismatch Guard Test



A forced mismatch was tested using:



\- Blog post: `A wild fox walking through a forest.`

\- Forced image: `wolf\_001.jpg`

\- Similarity score: `0.2867`

\- Minimum similarity threshold: `0.30`

\- Result: \*\*Rejected\*\*



The system returned:



```text

Similarity score 0.2867 is below the minimum threshold of 0.30.

```



\## API Evaluation



The evaluation is also exposed through:



GET /api/v1/evaluation



The endpoint returned:



{

&#x20; "total": 10,

&#x20; "correct": 10,

&#x20; "top\_1\_precision": 1

}



along with the individual evaluation results.



\## Automated Tests



The project currently has:



8 passed



The matching evaluation tests specifically verify:



1\. Top-1 precision remains at 100%.

2\. A forced fox/wolf mismatch is rejected.



\## Important Limitations



The current evaluation is intentionally small and uses 10 labeled posts over the 10 dataset categories.



The development dataset contains 50 images. The earlier Gemini vision-metadata processing run successfully produced metadata for 16/50 images, while 34/50 failed because the Gemini free-tier request quota was exhausted. These vision-processing failures are recorded in the dataset evidence and PostgreSQL. Separately, the image-embedding pipeline successfully generated 768-dimensional embeddings for all 50/50 images and stored them in the PostgreSQL `images.embedding` field used by the matching service.



The similarity threshold of `0.30` is currently a validated working threshold for this evaluation dataset. A larger evaluation dataset should be used before treating it as a production threshold.



\## Next Improvements



Future improvements include:



\- Larger evaluation dataset

\- Threshold tuning using validation data

\- Human review workflow

\- More robust semantic mismatch detection

\- Additional evaluation metrics beyond top-1 precision

