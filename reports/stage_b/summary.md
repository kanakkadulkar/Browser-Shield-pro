## Reading A  (dev normals 8327, validation folds 3)

| feature | friend: tree AUC | friend: rank AUC | rebuilt: tree AUC | rebuilt: rank AUC |
|---|---|---|---|---|
| idle_ratio | 0.796 | 0.578 | 0.527 | 0.541 |
| lag_per_second | 0.921 | 0.918 | 0.721 | 0.706 |
| dom_per_second | 0.908 | 0.899 | 0.529 | 0.547 |
| network_per_second | 0.994 | 0.988 | 0.832 | 0.784 |
| event_loop_lag_ms | 0.982 | 0.830 | 0.814 | 0.710 |
| dom_mutation_count | 0.949 | 0.786 | 0.543 | 0.524 |
| network_request_count | 0.904 | 0.860 | 0.807 | 0.811 |
| post_request_count | 0.913 | 0.822 | 0.846 | 0.844 |
| unique_domains_contacted | 0.920 | 0.815 | 0.742 | 0.703 |
| visibility_hidden | 0.643 | 0.654 | 0.512 | 0.514 |
| visibility_changes | 0.829 | 0.510 | 0.504 | 0.503 |

| model | friend | rebuilt |
|---|---|---|
| all 11 features | 1.000 | 0.976 |
| signal channels only | 1.000 | 0.974 |
| non-signal channels only | 0.997 | 0.545 |

Rebuilt, by strength tier:

| tier | attacks | all-feature AUC | non-signal AUC | best single feature (AUC) |
|---|---|---|---|---|
| weak | 709 | 0.958 | 0.556 | event_loop_lag_ms (0.817) |
| medium | 697 | 0.983 | 0.534 | network_per_second (0.854) |
| strong | 675 | 0.989 | 0.546 | post_request_count (0.911) |

## Reading B  (dev normals 1725, validation folds 2)

| feature | friend: tree AUC | friend: rank AUC | rebuilt: tree AUC | rebuilt: rank AUC |
|---|---|---|---|---|
| idle_ratio | 0.705 | 0.666 | 0.477 | 0.504 |
| lag_per_second | 0.890 | 0.913 | 0.658 | 0.707 |
| dom_per_second | 0.816 | 0.881 | 0.456 | 0.535 |
| network_per_second | 0.983 | 0.971 | 0.806 | 0.739 |
| event_loop_lag_ms | 0.991 | 0.841 | 0.793 | 0.718 |
| dom_mutation_count | 0.779 | 0.775 | 0.497 | 0.507 |
| network_request_count | 0.857 | 0.856 | 0.772 | 0.806 |
| post_request_count | 0.872 | 0.806 | 0.800 | 0.833 |
| unique_domains_contacted | 0.883 | 0.794 | 0.708 | 0.679 |
| visibility_hidden | 0.633 | 0.665 | 0.496 | 0.504 |
| visibility_changes | 0.766 | 0.517 | 0.518 | 0.523 |

| model | friend | rebuilt |
|---|---|---|
| all 11 features | 1.000 | 0.935 |
| signal channels only | 1.000 | 0.928 |
| non-signal channels only | 0.903 | 0.479 |

Rebuilt, by strength tier:

| tier | attacks | all-feature AUC | non-signal AUC | best single feature (AUC) |
|---|---|---|---|---|
| weak | 138 | 0.888 | 0.478 | event_loop_lag_ms (0.779) |
| medium | 149 | 0.942 | 0.486 | network_per_second (0.816) |
| strong | 140 | 0.976 | 0.472 | post_request_count (0.875) |
