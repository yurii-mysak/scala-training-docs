# Coding Challenges

LeetCode-style problems organized by pattern and difficulty. All solutions in Scala.

## Patterns Reference

- [LeetCode Patterns Guide](leetcode_patterns.md) — DFS, BFS, two-pointer, sliding window, etc.

---

## Easy

| # | Problem | File | Pattern | Key Concept |
|---|---------|------|---------|-------------|
| 1 | Remove Element | [RemoveElement.md](RemoveElement.md) | Two Pointer | In-place array modification |
| 2 | Two Sum | [task1_two_sum.md](task1_two_sum.md) | Hash Map | Complement lookup |
| 3 | Merge Sorted Array | [MergeSortedArray.md](MergeSortedArray.md) | Two Pointer | Merge from end |
| 4 | Remove Duplicates (Sorted) | [RemoveDuplicatesSorted.md](RemoveDuplicatesSorted.md) | Two Pointer | Slow/fast pointer |
| 5 | Kids with Max Candies | [MaxCandies.md](MaxCandies.md) | Array | Simple iteration |
| 6 | Valid Palindrome | [IsValidPalindrome.md](IsValidPalindrome.md) | Two Pointer | Left/right convergence |
| 7 | Climbing Stairs | [ClimbingStairs.md](ClimbingStairs.md) | DP | Fibonacci variant |
| 8 | Reverse Words | [ReverseWords.md](ReverseWords.md) | String | Split/reverse/join |
| 9 | Reverse Vowels | [ReverseVowels.md](ReverseVowels.md) | Two Pointer | Selective swap |
| 10 | Valid Parentheses | [task3_valid_parentheses.md](task3_valid_parentheses.md) | Stack | Bracket matching |
| 11 | Can Place Flowers | [CanPlaceFlowers.md](CanPlaceFlowers.md) | Greedy | Adjacent check |
| 12 | Is Subsequence | [IsSubSequence.md](IsSubSequence.md) | Two Pointer | Sequential match |
| 13 | Best Time to Buy/Sell Stock | [task5_best_time_to_buy_and_sell_stock.md](task5_best_time_to_buy_and_sell_stock.md) | Greedy/DP | Track min price |
| 14 | Majority Element | [MajorityElement.md](MajorityElement.md) | Boyer-Moore | Voting algorithm |
| 15 | Symmetric Tree | [task10_symmetric_tree.md](task10_symmetric_tree.md) | Tree/Recursion | Mirror comparison |
| 16 | GCD of Strings | [GreatestCommonDividerOfStrings.md](GreatestCommonDividerOfStrings.md) | Math/String | GCD on lengths |
| 17 | Alternate Merge | [AlternateMerge.md](AlternateMerge.md) | Two Pointer | Interleave arrays |
| 18 | Reverse Linked List | [task2_reverse_linked_list.md](task2_reverse_linked_list.md) | Linked List | Pointer reversal |
| 19 | Merge Two Sorted Lists | [task4_merge_two_sorted_lists.md](task4_merge_two_sorted_lists.md) | Linked List | Merge with dummy head |
| 20 | Parse Integer | [parseInt.md](parseInt.md) | String | Edge case handling |

## Medium

| # | Problem | File | Pattern | Key Concept |
|---|---------|------|---------|-------------|
| 21 | Maximum Subarray | [task6_maximum_subarray.md](task6_maximum_subarray.md) | DP | Kadane's algorithm |
| 22 | Best Buy/Sell (variants) | [BestBuySell.md](BestBuySell.md) | DP/Greedy | Multiple transaction variants |
| 23 | Product Except Self | [ArrayProductExceptSelf.md](ArrayProductExceptSelf.md) | Prefix/Suffix | Left-right product arrays |
| 24 | Longest Substring No Repeat | [task7_longest_substring_without_repeating_characters.md](task7_longest_substring_without_repeating_characters.md) | Sliding Window | Hash set + window |
| 25 | Letter Combinations (Phone) | [task8_letter_combinations_of_a_phone_number.md](task8_letter_combinations_of_a_phone_number.md) | Backtracking | Recursive generation |
| 26 | Generate Parentheses | [task9_generate_parentheses.md](task9_generate_parentheses.md) | Backtracking | Open/close count |
| 27 | Binary Tree Level Order | [task11_binary_tree_level_order_traversal.md](task11_binary_tree_level_order_traversal.md) | BFS | Queue-based traversal |
| 28 | Subsets | [task16_subsets.md](task16_subsets.md) | Backtracking | Power set generation |
| 29 | Jump Game | [JumpGame.md](JumpGame.md) | Greedy | Max reachable index |
| 30 | Increasing Triplets | [IncreasingTriplets.md](IncreasingTriplets.md) | Greedy | Track first/second smallest |
| 31 | Number of Islands | [task12_number_of_islands.md](task12_number_of_islands.md) | DFS/BFS | Grid flood fill |
| 32 | Course Schedule | [task13_course_schedule_topological_sort.md](task13_course_schedule_topological_sort.md) | Topological Sort | Cycle detection in DAG |
| 33 | LRU Cache | [task14_lru_cache.md](task14_lru_cache.md) | Design | HashMap + doubly linked list |
| 34 | BFS/DFS Traversals | [task21_bfs_dfs.md](task21_bfs_dfs.md) | Graph | Traversal comparison |
| 35 | Rotate Array | [RotateArray.md](RotateArray.md) | Array | Reverse trick |
| 36 | Divide String (K groups) | [DivideStringSubgroupK.md](DivideStringSubgroupK.md) | String | Chunking logic |
| 37 | Longest Harmonious Subseq | [LongestHarmoniusSubSequence.md](LongestHarmoniusSubSequence.md) | Hash Map | Frequency counting |

## Hard

| # | Problem | File | Pattern | Key Concept |
|---|---------|------|---------|-------------|
| 38 | Serialize/Deserialize Binary Tree | [task18_serialize_and_deserialize_binary_tree.md](task18_serialize_and_deserialize_binary_tree.md) | Tree/Design | Preorder + null markers |
| 39 | Trapping Rain Water | [task19_trapping_rain_water.md](task19_trapping_rain_water.md) | Two Pointer/Stack | Left-right max tracking |
| 40 | Sliding Window Maximum | [task20_sliding_window_maximum.md](task20_sliding_window_maximum.md) | Monotonic Deque | Decreasing deque window |

## Patterns Quick Reference

| Pattern | Problems | Typical Complexity |
|---------|----------|-------------------|
| Two Pointer | #1,3,4,6,9,12,17 | O(n) |
| Sliding Window | #24,40 | O(n) |
| Hash Map | #2,37 | O(n) |
| Stack/Deque | #10,39,40 | O(n) |
| DFS/BFS | #15,27,31,34 | O(V+E) |
| Backtracking | #25,26,28 | O(2^n) |
| Dynamic Programming | #7,21,22 | O(n) |
| Greedy | #11,13,29,30 | O(n) |
| Topological Sort | #32 | O(V+E) |
