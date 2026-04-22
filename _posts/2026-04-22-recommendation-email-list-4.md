---
title: Content Recommendation for April, 2026
date: 2026-04-22 12:45:00 +0800
categories: [Content Recommendation]
tags: [Agent Memory, Rust, NotebookLM]
pin: false
---

Hey there! Thanks for subscribing to my content recommendation posts. In this series, I share articles, videos, projects, and ideas that I recently found interesting, insightful, or genuinely helpful.

This edition contains content I curated during April, 2026. In this month, I developped several open-source projects using Claude Code, Trae, and OpenClaw. I finished my first commercial delivery of semantic operators in a relational database, and would divert my attention to the agent memory systems.

## ONE NotebookLM to understand academic papers

Google's NotebookLM has become an important tool for me to read a lot of papers, or better say, to figure out how a certain field works. It can absorb information from multiple sources, like PDFs, websites, images, audio, etc. You can put related paper PDF, github repo, websites into it and start asking questions. The agent will answer your questions based on the materials, and cite the exact content in the material, so there is much less hallucination. This funcionality is perfect to understand a lot of papers quickly.

For example, I put the MemoryBank's paper PDF file in it and ask "How does MemoryBank work? How does it store the memory and how does it retrieve content into its memory?"

NotebookLM gives me the following answer. Note that each number is clickable and will give you the exact reference to check facts.


MemoryBank is a long-term memory mechanism designed to transform static large language models into adaptive agents, particularly for personalized scenarios like emotional companions[1][2]. It operates through three main pillars: memory storage, a memory retriever, and a memory updater[3].

1. How MemoryBank Stores Memory

MemoryBank is classified as token-level, Flat Memory (1D), meaning it stores information as discrete, externally accessible units without an explicit complex topology like a graph[4][5]. It constructs a dynamic, multi-layered "warehouse" consisting of three types of information:

- Chronological Dialogue Records: It logs multi-turn conversations in detail, using timestamps to create an ordered narrative of all past interactions [6].

- Hierarchical Event Summaries: To prevent information overload, it distills verbose dialogues into concise daily summaries, which are further synthesized into a "global summary" of significant events[7].

- Dynamic User Portraits: The system assessments user personality traits and emotions daily, aggregating these insights into a global understanding of the user’s personality to tailor future responses[8][9].

2. How MemoryBank Retrieves Content

MemoryBank utilizes a dual-tower dense retrieval model to recall relevant information during real-time conversations[10]. The process works as follows:

- Vectorization: Every conversation turn and event summary (a "memory piece") is pre-encoded into a contextual vector representation using an encoder model[10]. In practice, it uses models like MiniLM for English or Text2vec for Chinese[11].

- Indexing: These vector representations are indexed using FAISS (Facebook AI Similarity Search) to ensure efficient retrieval even as the memory warehouse grows[12].

- Querying: During an interaction, the current conversation context is encoded into a vector that serves as a query to search the index for the most semantically relevant memories[11][12].

- Prompt Augmentation: The retrieved memories, along with the global user portrait and event summaries, are organized into a "memory-augmented prompt" for the LLM to generate a personalized response[13].

3. Memory Updating and Forgetting

To mimic human-like behavior, MemoryBank incorporates an updating mechanism inspired by the Ebbinghaus Forgetting Curve[1][14].

Memory Decay: Memories naturally decay over time according to an exponential model (R=e 
−t/S
 ), where R is retention, t is time elapsed, and S is memory strength[15].
- Reinforcement: When a memory piece is successfully recalled during a conversation, its strength (S) increases and its time counter (t) resets to zero, making it persist longer in the system[15].

- Selective Forgetting: This allows the agent to prioritize significant or frequently accessed information while gradually "forgetting" less important details from the distant past[1][12].

Would you like to know more about the "SiliconFriend" chatbot that was built using this MemoryBank architecture?

NotebookLM is basically a more trustworthy chatbot and I find it best at accelerating paper reading.

## THREE potentially interesting projects I developped

[AI Creator Vault](https://github.com/legendPerceptor/aicreatorvault) is an asset management platform for AI creators, helping you securely store, organize, and retrieve AI-generated images, prompts, and other creative assets. It can easily be deployed via docker, and I've deployed to my personal NAS. It works the same way if you deploy in your WSL or macOS. If you don't yet have your own data but want to play with the project to see what it can do, you can crawl some images and prompts via this project [AI Art Crawler](https://github.com/legendPerceptor/ai-art-crawler).


[pg_semantic_operators](https://github.com/legendPerceptor/pg_semantic_operators) is a PostgreSQL extension providing AI-powered query and filtering capabilities. The first selling point is the multi-modality operators, including ai_filter for text, ai_image_filter for images, and ai_audio_filter, etc. These operators are written in Python and can be installed via postgres extension, meaning there is no need to recompile the database system. The second selling point is the ai_query operator, which is essentially a text-to-sql or NL2SQL system. It features knowing the data schema and other semantic operator declarations, thus able to arrange these newly defined operators alongside traditional database sqls.


[Agent Memory](https://github.com/legendPerceptor/agent-memory) is a tiered memory system for AI Agents, supporting vector retrieval, auto-evolution, and knowledge graph. Based on my experience using OpenClaw as a secretarial assistant, when and how to retrieve memory remains an open problem. I hope to evolve this project overtime to incorporate recent advancements in agent memory research.


## FOUR basic Rust techniques to know

We will look at some `easy` LeetCode questions to elaborate some fundamental concepts in Rust language.

### How to deal with negative index?

Let's look at a simple array mergeing problem. The problem is available on [LeetCode: 88. Merge Sorted Array](https://leetcode.com/problems/merge-sorted-array/).

You are given two integer arrays `nums1` and `nums2`, sorted in non-decreasing order, and two integers `m` and `n`, representing the number of elements in `nums1` and `nums2` respectively. The goal is to merge nums1 and nums2 into a single array sorted in non-decreasing order.

We hope to store the result in `nums1` instead of creating a new result array. The array `nums1` is allocated with `m + n` positions already.

It is easy to think of building the array from tail, but the index in rust is of `usize` type. How do we handle the problem of the index going down to -1? Below is a solution --- using the "as isize" and "as usize" technique to convert the type so we can iterate to -1 with a isize variable but use it as index by converting it to usize.

```rust
impl Solution {
    pub fn merge(nums1: &mut Vec<i32>, m: i32, nums2: &mut Vec<i32>, n: i32) {
        let mut i = m as isize - 1;           // last valid element in nums1
        let mut j = n as isize - 1;           // last element in nums2
        let mut k = (m + n) as isize - 1;     // last position in nums1

        while j >= 0 {
            if i >= 0 && nums1[i as usize] > nums2[j as usize] {
                nums1[k as usize] = nums1[i as usize];
                i -= 1;
            } else {
                nums1[k as usize] = nums2[j as usize];
                j -= 1;
            }
            k -= 1;
        }
    }
}
```

### How to deal with match, Rc, RefCell?

Let's look at the [LeetCode 100. Same Tree](https://leetcode.com/problems/same-tree/description/) problem. Given the roots of two binary trees p and q, write a function to check if they are the same or not.

```rust
use std::rc::Rc;
use std::cell::RefCell;

// Definition for a binary tree node.
#[derive(Debug, PartialEq, Eq)]
pub struct TreeNode {
  pub val: i32,
  pub left: Option<Rc<RefCell<TreeNode>>>,
  pub right: Option<Rc<RefCell<TreeNode>>>,
}

impl TreeNode {
  #[inline]
  pub fn new(val: i32) -> Self {
    TreeNode {
      val,
      left: None,
      right: None
    }
  }
}
```

This is a rather simple problem, but we want to solve it in a Rust-idiomatic way. To deal with the Rust code for this problem, we need to be equipped with some basic knowledge of `match`, `Rc`, `RefCell`, `Option`.

- **`Option<T>`**: Rust doesn't have `null`. Instead, `Option<T>` is either `Some(value)` or `None`. A tree node's `left` and `right` children are `Option<Rc<RefCell<TreeNode>>>`, meaning they may or may not exist.

- **`Rc<T>` (Reference Counted)**: In Rust, each value has a single owner. But a tree node might be referenced from multiple places (e.g., traversing from parent, or holding a reference during recursion). `Rc` enables shared ownership via reference counting — when the last `Rc` pointing to a value is dropped, the value is freed.

- **`RefCell<T>`**: Rust enforces borrow rules (one mutable reference **or** multiple immutable references) at compile time. For tree structures, this is too strict — you may need to mutate a node after borrowing it through `Rc`. `RefCell` moves the borrow check to runtime, allowing you to call `.borrow()` or `.borrow_mut()` on the same value even though it's behind a shared reference (`Rc`).

- **`match`**: Pattern matching in Rust. By matching on a tuple of two `Option` values `(p, q)`, we handle all combinations: both `None`, one `None`, or both `Some` — each case with a clear, explicit branch.

With these building blocks in mind, here is the final solution.

```rust
use std::rc::Rc;
use std::cell::RefCell;

impl Solution {
    pub fn is_same_tree(
        p: Option<Rc<RefCell<TreeNode>>>,
        q: Option<Rc<RefCell<TreeNode>>>
    ) -> bool {
        match (p, q) {
            (None, None) => true,
            (Some(_), None) | (None, Some(_)) => false,
            (Some(p_node), Some(q_node)) => {
                let p_ref = p_node.borrow();
                let q_ref = q_node.borrow();

                p_ref.val == q_ref.val
                    && Self::is_same_tree(p_ref.left.clone(), q_ref.left.clone())
                    && Self::is_same_tree(p_ref.right.clone(), q_ref.right.clone())
            }
        }
    }
}
```

A few points to note: (1) the clone here is cheap because it is just adding a reference count to an `Rc` object. (2) the borrow() call here is necessary because it signals the compiler to check the borrowing rules at runtime, otherwise the code cannot get through the very strict Rust compiler. (3) We did not write any return statement because in Rust, everything is an expression unless explicitly a statement. An expression evaluates to a value. A statement has a semicolon. The key rule: semicolon changes everything.

### How to pass mutable reference and define arrays?

For this, we look at [LeetCode: 62. Unique Path](https://leetcode.com/problems/unique-paths/description/). To define a 2-dimensional array, it is very easy if we use `vec!` macro. We can define an array full of 0 and of m x n with `let array = vec![vec![0; n]; m];`.

You might think of exploring every path recursively, but it is too slow. Nonetheless, it is good to put that solution here to show how to pass a mutable reference, how to modify the value of a mutable reference, and why calling the function recursively will pass `counter` differently.

```rust
impl Solution {
    fn visit(cur_x: i32, cur_y: i32, m: i32, n: i32, counter: &mut i32) {
        if cur_x == n - 1 && cur_y == m - 1 {
            *counter += 1;
            return;
        }

        if cur_x + 1 < n {
            Self::visit(cur_x + 1, cur_y, m, n, counter); // There is no &mut because the counter here is alreayd a mutable reference
        }
        if cur_y + 1 < m {
            Self::visit(cur_x, cur_y + 1, m, n, counter);
        }
    }

    pub fn unique_paths(m: i32, n: i32) -> i32 {
        let mut counter: i32 = 0; // The counter here is a mutable variable, not a mutable reference
        Self::visit(0, 0, m, n, &mut counter); // There is a &mut here because we want to pass it as a mutable reference
        return counter;
    }
}
```

The above method is extremely inefficient, the problem can be solved via dynamic programming.

Here is the final solution using dynamic programming.

```rust
impl Solution {
    pub fn unique_paths(m: i32, n: i32) -> i32 {
        let m = m as usize;
        let n = n as usize;
        let mut dp = vec![vec![1; n]; m];

        for i in 1..m {
            for j in 1..n {
                dp[i][j] = dp[i - 1][j] + dp[i][j - 1];
            }
        }

        dp[m - 1][n - 1]
    }
}
```

### How to process each byte in a String?

We look at [LeetCode: 8. String to Integer(atoi)](https://leetcode.com/problems/string-to-integer-atoi/) for this knowledge.

```rust
impl Solution {
    pub fn my_atoi(s: String) -> i32 {
        let bytes = s.as_bytes();
        let mut i = 0;
        let n = bytes.len();

        // 1. Skip leading whitespace
        while i < n && bytes[i] == b' ' {
            i += 1;
        }

        // 2. Handle sign
        let mut sign = 1;
        if i < n {
            if bytes[i] == b'-' {
                sign = -1;
                i += 1;
            } else if bytes[i] == b'+' {
                i += 1;
            }
        }

        // 3. Parse digits
        let mut result: i32 = 0;

        while i < n && bytes[i].is_ascii_digit() {
            let digit = (bytes[i] - b'0') as i32;

            // 4. Handle overflow BEFORE multiplying
            if result > (i32::MAX - digit) / 10 {
                return if sign == 1 { i32::MAX } else { i32::MIN };
            }

            result = result * 10 + digit;
            i += 1;
        }

        result * sign
    }
}
```


## FIVE English words to learn

> I recommend visiting [Merriam-Webster Dictionary](https://www.merriam-webster.com/dictionary/) to understand each word better and find more examples.
{: .prompt-info }

**holistic**: relating to or concerned with complete systems rather than with individual parts. Example: "This design helps the system encode knowledge that is more holistic and more deeply contextualized."

**hindrance**: a person, thing, or situation that interferes with, slows down, or obstructs progress. Example: "Despite this, a notable hindrance remains --- the deficiency of a long-term memory mechanism within these models."

**rapport**: a friendly, harmonious relationship characterized especially by agreement, mutual understanding, or empathy that makes communication possible or easy. Example: "For instance, personal AI companions need to recall past conversations for rapport building."

**corroborate**:  to support or help prove with evidence or authority : make more certain. Example: "These findings corroborate the potential of MemoryBank to significantly improve the performance of LLMs into long-term interaction scenarios."

**meticulous**: very careful about doing something in an extremely accurate and exact way. Example: "Memory storage, the warehouse of MemoryBank, is a robust data repository holding a meticulous array of information."
