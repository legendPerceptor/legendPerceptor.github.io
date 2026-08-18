---
title: 经典算法以及C++/Python临时抱佛脚指南
date: 2026-08-17 21:45:00 +0800
categories: [Tutorial]
tags: [algorithm, C++, Python, 算法]
pin: false
math: true
---

在AI盛行的今天，仍有一些比赛、技术面试、考试需要我们熟练地掌握各类算法，并能用一款编程语言在尽可能短的时间内手搓代码解决问题。这项技能从我们学习编程的第一天就开始培养，又在实际工作中逐渐生疏——我们常常遇到曾经已经解决的问题再度变成不会的难题的情况，对STL的熟练度也往往会成为成败的分水岭。笔者最近正好需要在短时间内准备一场比赛，为了不坑队友，决定花一点时间梳理一下常用的知识。

本文不是按照由难到易或者由易到难的顺序组织的，而是按照笔者多年来对**容易遗忘程度**进行排序的，排在前面的是那些如果背不出基本只能放弃的特定算法，接着是一些需要用到STL关键特性的解决方案（如果不会STL，手搓将耗费过多时间），然后是经典的各类算法知识点。希望读者也能从中获益，在临时抱佛脚的时候会感激这篇文章的存在。

## 线段树 - Segment Tree

首先讲一道最基础的需要用线段树解决的题目: [LeetCode 307 Range Sum Query](https://leetcode.com/problems/range-sum-query-mutable)。这道题几乎是线段树的定义和解释——对一个数组保持下面两个特性：(1)支持更新其中的任何一个元素；(2)能快速计算`[left, right]`之间元素的和。

线段树的特性是建树复杂度`O(n)`, 单点修改`O(log n)`，区间求和`O(log n)`。如果不会线段树的实现，区间求和这部分很难临场想出好办法，最笨的办法需要`O(n)`的复杂度计算每次求和，导致超时错误。

假设我们有`nums=[1, 3, 5, 7]`这个数组，线段树的结构大概如下所示。叶子节点都只有一个元素，每个树节点存的是它子节点元素的和。

```text
                      [0,3] = 16
                     /          \
              [0,1] = 4        [2,3] = 12
               /     \           /      \
          [0,0]=1  [1,1]=3  [2,2]=5  [3,3]=7
```

如果元素个数不是2的次方，比如5个元素，`nums=[1, 3, 5, 7, 4]`，这棵树会长成下面这样：

```text
                              [0,4] = 20
                           /               \
                    [0,2] = 9              [3,4] = 11
                   /         \             /          \
             [0,1] = 4     [2,2] = 5  [3,3] = 7   [4,4] = 4
              /      \
        [0,0] = 1  [1,1] = 3
```

针对每个节点下标`si`，访问子节点的方法是

```cpp
left_child = 2 * si + 1;
right_child = 2 * si + 2;
```

这棵树需要多少个节点？比较宽松快捷的方式是直接使用`4n`（节点数不可能超过4n），更节省空间的算法是`2 * pow(2, ceil(log2(n))) - 1`。这个计算公式的原理是这样的：

1. 一颗满二叉树的叶子节点有L个，那么它总共有2L-1个节点。
2. 把一个长度为n的数组作为完全二叉树的叶子节点，要塞下，这个完全二叉树有多少叶子节点？这个L需要是2的次方，并且至少有n那么大

$$L = 2^K \geq n \rightarrow K \geq log_2 n \rightarrow K = \lceil log_2 n \rceil \rightarrow L = 2^{\lceil log_2 n \rceil}$$

这棵线段树中的每个节点都表示了一个线段`[start, end]`，每个节点存储的信息就是这条线段的长度，叶子节点就是每个数组元素的值。

容易忘的是参数个数，可以这么记：
1. query需要(1)st - segment tree，一个用来存放线段树的数组，长度用前面的方法计算，简记`4n`;(2) ss - segment start，当前线段开始点;(3) se - segmemt end，当前线段结束点;(4) qs - query start，查询的起始点;(5) qe - query end，查询的终止点;(6) si - segment index，当前访问的线段节点下标；
2. build的时候没有query，所以少两个参数qs, qe；
3. update需要下标和差值，用一个额外接口函数包装一下。

建树、查询、更新的过程都是用二分查找的方式自顶向下遍历二叉树：
1. 建树的退出情况是当`ss==se`的时候存数组本身的元素值返回，否则就递归取两个子树的值之和，这个值取完都要更新到`st[si]`中。
2. 查询时当`[qs,qe]`包含了`[ss,se]`，说明当前这条线段被包含在查询中，直接返回当前节点的值，如果`[qs,qe]`完全在`[ss, se]`之外，说明当前这条线段不应被考虑直接返回0，否则用二分的方式继续找子树，求和就返回两个子树的和，求最大/最小值就返回两个子树的最大/最小值。
3. 更新的时候，如果下标`i`不在`[ss,se]`之内，说明与当前线段无关，直接返回；否则就更新当前节点的值加上 `st[i] +=diff`，然后递归更新子树。

下面是这道题的完整解法。

```cpp
/**
 * Your NumArray object will be instantiated and called as such:
 * NumArray* obj = new NumArray(nums);
 * obj->update(index,val);
 * int param_2 = obj->sumRange(left,right);
 *//**
 * Your NumArray object will be instantiated and called as such:
 * NumArray* obj = new NumArray(nums);
 * obj->update(index,val);
 * int param_2 = obj->sumRange(left,right);
 */
class NumArray {
public:
    int* segment_tree;
    int size;
    vector<int> nums;
    NumArray(vector<int>& nums) {
        this->size = 2*(int)pow(2, ceil(log2(nums.size())))-1; 
        this->segment_tree = new int[this->size];
        this->nums = nums;
        constructSTUtil(segment_tree, 0, nums.size()-1, 0);
    }
    
    void update(int index, int val) {
        int diff = val - nums[index];
        nums[index] = val;
        updateValueUtil(segment_tree, 0, nums.size()-1, index, diff, 0);
    }
    
    int sumRange(int left, int right) {
        return getSumUtil(segment_tree, 0, nums.size()-1, left, right, 0);
    }
    
    int getSumUtil(int* st, int ss, int se, int qs, int qe, int si) {
        if(qs<=ss && qe>=se){
            return st[si];
        }
        if(se<qs || ss > qe){
            return 0;
        }
        int mid = (ss+se)/2;
        return getSumUtil(st, ss, mid, qs, qe, 2*si+1) + getSumUtil(st, mid+1, se, qs, qe, 2*si+2);
    }
    
    void updateValueUtil(int *st, int ss, int se, int i, int diff, int si) {
        if(i<ss || i>se) {
            return;
        }
        st[si] = st[si] + diff;
        if(se!=ss) {
            int mid = (ss+se)/2;
            updateValueUtil(st, ss, mid, i, diff, 2*si+1);
            updateValueUtil(st, mid+1, se, i, diff, 2*si+2);
        }
    }
    
    int constructSTUtil(int* st, int ss, int se, int si) {
        if(ss==se){
            st[si] = nums[ss];
            return nums[ss];
        }
        int mid = (ss+se)/2;
        st[si] = constructSTUtil(st, ss, mid, si*2+1) + constructSTUtil(st, mid+1, se, si*2+2);
        return st[si];
    }
};
```

Python实现：

```python
from typing import List

class NumArray:

    def __init__(self, nums: List[int]):
        self.nums = nums.copy()

        # 找到不小于 n 的最小 2 的幂
        leaf_count = 1 << (len(nums) - 1).bit_length()

        # 具有 leaf_count 个叶子节点的满二叉树共有 2L - 1 个节点
        tree_size = 2 * leaf_count - 1
        self.segment_tree = [0] * tree_size

        self._build(0, len(nums) - 1, 0)

    def update(self, index: int, val: int) -> None:
        diff = val - self.nums[index]
        self.nums[index] = val

        self._update(
            segment_start=0,
            segment_end=len(self.nums) - 1,
            index=index,
            diff=diff,
            tree_index=0
        )

    def sumRange(self, left: int, right: int) -> int:
        return self._query(
            segment_start=0,
            segment_end=len(self.nums) - 1,
            query_start=left,
            query_end=right,
            tree_index=0
        )

    def _build(
        self,
        segment_start: int,
        segment_end: int,
        tree_index: int
    ) -> int:

        # 叶子节点
        if segment_start == segment_end:
            self.segment_tree[tree_index] = self.nums[segment_start]
            return self.nums[segment_start]

        mid = (segment_start + segment_end) // 2

        left_sum = self._build(
            segment_start,
            mid,
            tree_index * 2 + 1
        )

        right_sum = self._build(
            mid + 1,
            segment_end,
            tree_index * 2 + 2
        )

        self.segment_tree[tree_index] = left_sum + right_sum
        return self.segment_tree[tree_index]

    def _update(
        self,
        segment_start: int,
        segment_end: int,
        index: int,
        diff: int,
        tree_index: int
    ) -> None:

        # index 不在当前节点表示的区间中
        if index < segment_start or index > segment_end:
            return

        # 当前节点包含 index，因此节点和需要加上 diff
        self.segment_tree[tree_index] += diff

        # 如果不是叶子节点，继续递归更新子节点
        if segment_start != segment_end:
            mid = (segment_start + segment_end) // 2

            if index <= mid:
                self._update(
                    segment_start,
                    mid,
                    index,
                    diff,
                    tree_index * 2 + 1
                )
            else:
                self._update(
                    mid + 1,
                    segment_end,
                    index,
                    diff,
                    tree_index * 2 + 2
                )

    def _query(
        self,
        segment_start: int,
        segment_end: int,
        query_start: int,
        query_end: int,
        tree_index: int
    ) -> int:

        # 情况一：当前节点的区间完全被查询区间包含
        if query_start <= segment_start and segment_end <= query_end:
            return self.segment_tree[tree_index]

        # 情况二：当前节点的区间与查询区间完全没有交集
        if segment_end < query_start or segment_start > query_end:
            return 0

        # 情况三：部分重叠，分别查询左右子树
        mid = (segment_start + segment_end) // 2

        left_sum = self._query(
            segment_start,
            mid,
            query_start,
            query_end,
            tree_index * 2 + 1
        )

        right_sum = self._query(
            mid + 1,
            segment_end,
            query_start,
            query_end,
            tree_index * 2 + 2
        )

        return left_sum + right_sum
```

## 前缀树 Prefix Tree - Trie

[LeetCode 208. Implement Trie](https://leetcode.com/problems/implement-trie-prefix-tree/description/)。Prefix Tree主要用于高效地存储和查询大量字符串，特别适合处理与前缀有关的问题——可以判断一个完整单词是否存在，判断是否存在某个前缀，根据前缀寻找所有匹配的单词，在大量字符串中进行词典匹配。对于长度为`L`的字符串，插入、查询完整字符串、查询前缀、删除字符串都可以在`O(L)`的时间复杂度内完成。它的核心思想是**让具有相同前缀的字符串共享同一段路径**。

每个树节点包含一个`_isEnd`的标记位用于判断当前节点是否是一个词的结尾，还需要维护一个长度为所有种类字符总长度的字符集的`children`数组，这里因为只有英文字母，可以确定长度是26。

insert, search, startsWtih三个操作都是递归的，判断当前下标是否满足到达词末尾或到达prefix字符串末尾，如果尚未到达，从`children[cur_index]`继续进行下一步的操作，cur_index是字符串当前下标的字符对应到字符集的下标。退出的时候都是`index==word.size()`的时候，因为从一开始就是对`root->children`进行操作而不是`root`本身，只有到`index`到`word.size()`的时候才结束，不是`word.size()-1`的时候结束。

这个`children`也可以用哈希表实现，这样没有字符集的限制，递归的过程也可以不用函数调用，而用循环的方式更快完成，我们在Python实现中采用这种方式。

完整的C++实现如下所示:

```cpp
class TrieNode {
    std::vector<TrieNode*> children;
    bool _isEnd;
public:
    TrieNode() {
        this->children = std::vector<TrieNode*>(26, nullptr);
        this->_isEnd = false;
    }

    ~TrieNode() {
        for(int i=0;i<children.size();i++) {
            if(children[i] != nullptr) {
                delete children[i];
            }
        }
    }

    void insert(const string& word, int index) {
        if(index == word.size()){
            this->_isEnd = true;
            return;
        }
        int cur_index = word[index] - 'a';
        if(children[cur_index] == nullptr) {
            children[cur_index] = new TrieNode();
        }
        children[cur_index]->insert(word, index+1);
    }

    bool search(const string& word, int index) {
        if(index == word.size()) {
            if(_isEnd){
                return true;
            }else{
                return false;
            }
        }
        int cur_index = word[index] - 'a';
        if(children[cur_index] == nullptr){return false;}
        else{
            return children[cur_index]->search(word, index+1);
        }
    }

    bool startsWith(string prefix, int index) {
        if(index == prefix.size()) {
            return true;
        }
        int cur_index = prefix[index] - 'a';
        if(children[cur_index] == nullptr){return false;}
        else{
            return children[cur_index]->startsWith(prefix, index+1);
        }
    }

};

class Trie {
    TrieNode* root;
public:
    Trie() {
        root = new TrieNode();
    }

    ~Trie() {
        delete root;
    }
    
    void insert(string word) {
        root->insert(word, 0);
    }
    
    bool search(string word) {
        return root->search(word, 0);
    }
    
    bool startsWith(string prefix) {
        return root->startsWith(prefix, 0);
    }
};

/**
 * Your Trie object will be instantiated and called as such:
 * Trie* obj = new Trie();
 * obj->insert(word);
 * bool param_2 = obj->search(word);
 * bool param_3 = obj->startsWith(prefix);
 */
```

Python实现如下：

```python
class TrieNode:
        # Initialize your data structure here.
        def __init__(self):
            self.word=False
            self.children={}
    
    class Trie:
    
        def __init__(self):
            self.root = TrieNode()
    
        # @param {string} word
        # @return {void}
        # Inserts a word into the trie.
        def insert(self, word):
            node=self.root
            for i in word:
                if i not in node.children:
                    node.children[i]=TrieNode()
                node=node.children[i]
            node.word=True
    
        # @param {string} word
        # @return {boolean}
        # Returns if the word is in the trie.
        def search(self, word):
            node=self.root
            for i in word:
                if i not in node.children:
                    return False
                node=node.children[i]
            return node.word
    
        # @param {string} prefix
        # @return {boolean}
        # Returns if there is any word in the trie
        # that starts with the given prefix.
        def startsWith(self, prefix):
            node=self.root
            for i in prefix:
                if i not in node.children:
                    return False
                node=node.children[i]
            return True
            
    
    # Your Trie object will be instantiated and called as such:
    # trie = Trie()
    # trie.insert("somestring")
    # trie.search("key")
```

接下来是一个使用Trie的案例[LeetCode 211. Design Add and Search Words Data Structure](https://leetcode.com/problems/design-add-and-search-words-data-structure/description/)。

我们在C++中用哈希表实现一下，增强对前缀树的理解。由于有通配符的存在，search难以用循环实现，对通配符需要对所有children进行枚举判断是否存在一条路径满足条件。

```cpp
struct Node {
    std::unordered_map<char, Node*> children;
    bool is_end;
    Node(){
        this->is_end = false;
    }
};

class WordDictionary {
private:
    Node* root;
public:
    WordDictionary() {
        root = new Node();
    }
    
    void addWord(string word) {
        Node* p = root;
        int index;
        for(int i=0;i<word.size();i++) {
            char cur = word[i];
            if(p->children.find(cur) == p->children.end()) {
                p->children[cur] = new Node();
            }
            p = p->children[cur];
            if(i == word.size() - 1) {
                p->is_end = true;
            }
        }
    }
    
    bool search(string word) {  
        return searchImpl(word, 0, root);
    }

    bool searchImpl(const string& word, int index, Node* p) {
        if(index == word.size()) { 
            if(p->is_end) {
                return true;
            } else {
                return false;
            }
        }
        char cur = word[index];
        if(cur == '.') {
            bool found = false;
            for(auto it = p->children.begin(); it!=p->children.end(); it++) {
                found = found || searchImpl(word, index+1, it->second);
            }
            return found;
        } else {
            auto iter = p->children.find(cur);
            if(iter == p->children.end()) {
                return false;
            } else {
                return searchImpl(word, index+1, iter->second);
            }
        }
    }
};

/**
 * Your WordDictionary object will be instantiated and called as such:
 * WordDictionary* obj = new WordDictionary();
 * obj->addWord(word);
 * bool param_2 = obj->search(word);
 */
```

## Dijkstra 最短路径算法和优先队列

最短路径算法其实应该属于一个经典算法，但因为里面必须要用到优先队列，如果不及时复习很容易写不出来，我把它单独放在前面讲解。



## 经典算法和数据结构

### 哈希表 - Hash Map

哈希表可以用来在O(1)复杂度内判断过去是否遇到过相同值。需要熟练掌握，如果你忽视这种最简单的数据结构的话，你会发现多年不用，可能写不出来！

#### Two Sum

[LeetCode 1. Two Sum](https://leetcode.com/problems/two-sum/description/):给定一个数组和目标值，如何通过一遍遍历找出可以求和得到目标值的二元组下标？

这题简单的一点在于只需要找到一个解，因为题设只有一个符合条件的解，到后面Three Sum，我们会进一步解决多个解的问题。

关键在于掌握C++中`unordered_map`的使用方法（如何判断表中是否已有某个元素，如何往表中插入一个新值）。哈希表中的key是target减去当前元素的值（因为下次遇到这个key的值时，就说明找到了），value是当前元素的下标。

```cpp
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> map_;
        vector<int> result;
        for(int i=0;i<nums.size();i++) {
            if(map_.find(nums[i]) != map_.end()) {
                return vector<int>{map_[nums[i]], i};
            }
            map_[target - nums[i]] = i;
        }
        return vector<int>{};
    }
};
```

Python实现：

```python
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        storage = {}
        for index, num in enumerate(nums):
            if target - num in storage:
                return [storage[target - num], index]
            storage[num] = index           
        return []
```

#### Three Sum

[LeetCode 15. 3Sum](https://leetcode.com/problems/3sum/description/)。这题需要找出数组中所有不重复的三元组，求和等于0。比前面TwoSum复杂的在于解不止一个，而且不能出现重复。

这个问题的一个思路是，对数组中每个值$value_i$都可以往后用TwoSum把target设为$-value_i$来求得三元组，为了不出现重复的，可以对数组进行排序，并且在TwoSum内使用`std::set`来避免插入重复元素（这里每次插入的复杂度是O(log n)，排序的时间复杂度是$O(nlog n)$，前面这个操作是$O(n^2 log n)$，所以最后总的时间复杂度是$O(n^2 log n)$。这不是最优解，时间复杂度最优可以到$O(n^2)$，不过这是一个最容易想到的解决方案。

```cpp
class Solution {
public:
    std::set<std::pair<int, int>> twoSum(
        const std::vector<int>& nums,
        int start,
        int target
    ) {
        std::unordered_map<int, int> needed;
        std::set<std::pair<int, int>> result;

        for (int i = start; i < static_cast<int>(nums.size()); ++i) {
            auto it = needed.find(nums[i]);

            if (it != needed.end()) {
                result.insert({it->second, nums[i]});
            }

            // If a later number equals target - nums[i],
            // combine it with the current nums[i].
            needed[target - nums[i]] = nums[i];
        }

        return result;
    }

    std::vector<std::vector<int>> threeSum(std::vector<int>& nums) {
        std::vector<std::vector<int>> final_result;
        std::sort(nums.begin(), nums.end());

        int n = static_cast<int>(nums.size());

        for (int i = 0; i + 2 < n; ++i) {
            // Avoid generating the same first element again.
            if (i > 0 && nums[i] == nums[i - 1]) {
                continue;
            }

            auto results = twoSum(nums, i + 1, -nums[i]);

            for (const auto& [first, second] : results) {
                final_result.push_back({
                    nums[i],
                    first,
                    second
                });
            }
        }

        return final_result;
    }
};
```

上面这种方法还是会导致产生重复元组，是利用了`std::set`的方式进行清除，一个更好的方式是用TwoPointers的思想，从源头上避免重复，这个方案的时间复杂度是$O(n^2)$。这里的关键思路是在从小到大排序的情况下，求和想要值变大，一定是左边的pointer右移，要想值变小，一定是右边的pointer往左移。

```cpp
class Solution {
public:
    std::vector<std::vector<int>> threeSum(std::vector<int>& nums) {
        std::vector<std::vector<int>> result;
        std::sort(nums.begin(), nums.end());

        int n = static_cast<int>(nums.size());

        for (int i = 0; i + 2 < n; ++i) {
            // Once nums[i] is positive, the remaining values are also
            // positive, so their sum cannot be zero.
            if (nums[i] > 0) {
                break;
            }

            // Skip duplicate choices for the first number.
            if (i > 0 && nums[i] == nums[i - 1]) {
                continue;
            }

            int left = i + 1;
            int right = n - 1;

            while (left < right) {
                int sum = nums[i] + nums[left] + nums[right];

                if (sum < 0) {
                    ++left;
                } else if (sum > 0) {
                    --right;
                } else {
                    result.push_back({
                        nums[i],
                        nums[left],
                        nums[right]
                    });

                    ++left;
                    --right;

                    // Skip duplicate second numbers.
                    while (left < right &&
                           nums[left] == nums[left - 1]) {
                        ++left;
                    }

                    // Skip duplicate third numbers.
                    while (left < right &&
                           nums[right] == nums[right + 1]) {
                        --right;
                    }
                }
            }
        }

        return result;
    }
};
```


### 红黑树/平衡树 - std::set

一道经典的问题是选择最匹配的内存部署虚拟机：一批物理机记录于数组`capacities`中，`capacities[i]`表示编号为`i`的物理机的初始内存大小；同时给出一批虚拟机部署请求`requests`，`requests[i]`表示某虚拟机的所需内存。请按如下规则依次处理每个虚拟机部署请求，并返回每个虚拟机部署所在物理机的编号（或者-1）：
- 如果所有物理机的可用内存不足，则部署失败，返回-1
- 否则，在满足虚拟机所需内存的所有物理机中，选择可用内存最小的；若仍有多台，选择其中编号最小的。

这题最重要的是了解平衡树的特性在C++中如何使用，可以使用`std::set`来完成。`std::set`是通过平衡树实现的，通常是红黑树（如果不会用要现场手搓红黑树，想想就酸爽）。

需要记住的知识点主要有这两点：(1)了解C++ STL中自定义排序的写法，最方便的是使用lambda函数；(2) `std::set`的`lower_bound`函数的用法来进行O(log n)的搜索找到“第一个容量大于等于请求”。这个`lower_bound`的特性是优先队列没有的，所以这题需要平衡树来解决，而不是使用`std::priority_queue`。

```cpp
struct Machine {
    int capacity;
    int id;
    Machine(int capacity, int id):capacity(capacity), id(id) {}
    Machine():capacity(0), id(-1){}
};

class Solution {
    vector<int> DispatchRequests(const vector<int>& capacities, const vector<int>& requests) {
        auto cmp = [](const Machine& a, const Machine& b) {
            if(a.capacity == b.capacity) {return a.id < b.id;}
            return a.capacity < b.capacity;
        };
        std::set<Machine, decltype(cmp)> container(cmp); // C++ 20之后可以不传递cmp参数到构造函数中
        for (size_t i=0;i<capacities.size(); i++) {
            container.insert(Machine{capacities[i], i});
        }
        std::vector<int> result;
        result.reserve(requests.size()); // 减少push_back重新分配内存的时间开销
        for(auto request: requests) {
            auto it = container.lower_bound(Machine{request, -1});
            if(it != container.end()) {
                Machine tmp = *it;
                result.push_back(tmp.id);
                container.erase(it);
                tmp.capacity -= request;
                container.insert(tmp);
            } else {
                result.push_back(-1);
            }
        }
        return result;
    }
};
```

Python的实现方式 —— Python没有内置的红黑树实现，需要一个三方库`sortedconatiners`中的`SortedList`。

```python
from typing import List
from sortedcontainers import SortedList

class Solution:
    def dispatch_requests(
        self,
        capacities: List[int],
        requests: List[int]
    ) -> List[int]:

        # 每个元素为 (剩余容量, 物理机编号)
        machines = SortedList(
            (capacity, machine_id)
            for machine_id, capacity in enumerate(capacities)
        )

        result = []

        for request in requests:
            # 寻找第一个不小于 (request, -1) 的元素
            index = machines.bisect_left((request, -1))

            if index == len(machines):
                result.append(-1)
                continue

            capacity, machine_id = machines.pop(index)

            result.append(machine_id)

            # 更新物理机的剩余容量
            machines.add((capacity - request, machine_id))

        return result
```


### Two Pointers

#### Container With Most Water

[LeetCode 11. Container With Most Water](https://leetcode.com/problems/container-with-most-water/description/) 是经典的Two Pointers入门题

主要思想是两边的柱子只有更矮的那根往中间走，才可能让水面变高，从而围出更大的面积。具体实现如下：

```cpp
class Solution {
public:
    int maxArea(vector<int>& height) {
        int left = 0, right = height.size() - 1;
        int cur_max = std::min(height[left], height[right]) * (right - left);
        while(left < right) {
            if(height[left] < height[right]) {
                left++;
            } else {
                right--;
            }
            cur_max = std::max(cur_max, std::min(height[left], height[right]) * (right - left));
        }
        return cur_max;
    }
};
```

前面提到的Three Sum问题是另外一个经典的TwoPointers可以解决的场景。

