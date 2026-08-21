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

## 最短路径算法和优先队列

最短路径算法其实应该属于普通的经典算法，但因为里面同时需用到优先队列，如果不及时复习很容易写不出来，我把它单独放在前面讲解。

### Dijkstra 算法

[LeetCode 743. Network Delay Time](https://leetcode.com/problems/network-delay-time/)是一道经典的**边权非负**的最短路径问题，求的是从一个给定点出发发射信号，到所有节点都能收到所需的最短时间。这类问题可以用Dijkstra算法解决。

Dijkstra需要优先队列的原因是**每次需要从当前尚未处理的节点中，找到起点距离最小的节点**，如果每次遍历所有节点取最小值，复杂度为 $O(V^2)$，使用优先队列后，复杂度为 $O((V+E) \log V)$，对于一个连通图，边的数量大于等于V-1，所以这个复杂度可以简记为$O(E \log V)$.

Dijkstra的核心性质是：当前距离最小的节点出堆后，其最短路径已经确定，不会再被后续路径缩短，这一点必须要求边权非负。

Dijkstra找到到某一个点的最短路径和找到到所有点的最短路径所需的流程是一样的。

该算法的通用实现方式如下：

```cpp
using State = pair<long long, int>;
// {从起点到当前节点的距离, 当前节点}

std::vector<long long> dijkstra(
    int start,
    const std::vector<std::vector<std::pair<int, int>>>& graph
) {
    int n = graph.size();
    const long long INF = std::numeric_limits<long long>::max();

    std::vector<long long> distance(n, INF);
    distance[start] = 0;

    std::priority_queue<
        State,
        std::vector<State>,
        std::greater<State>
    > min_heap;

    min_heap.push({0, start});

    while (!min_heap.empty()) {
        auto [current_distance, node] = min_heap.top();
        min_heap.pop();

        // 堆中可能存在同一个节点的旧距离
        if (current_distance > distance[node]) {
            continue;
        }

        for (auto [next_node, weight] : graph[node]) {
            long long new_distance =
                current_distance + weight;

            if (new_distance < distance[next_node]) {
                distance[next_node] = new_distance;
                min_heap.push({
                    new_distance,
                    next_node
                });
            }
        }
    }
    return distance;
}
```

下面是将这个算法用于解决LeetCode 743的完整实现：

```cpp
class Solution {
public:
    const int INF = std::numeric_limits<int>::max();
    
    std::vector<int> dijkstra(
        int start,
        const std::vector<std::vector<std::pair<int, int>>>& graph
    ) {
        int n = graph.size();
        
        std::vector<int> distance(n, INF);
        distance[start] = 0;

        std::priority_queue<
            std::pair<int, int>,
            std::vector<std::pair<int, int>>,
            std::greater<std::pair<int,int>>
        > min_heap;

        min_heap.push({0, start});

        while(!min_heap.empty()) {
            auto [current_distance, node] = min_heap.top();
            min_heap.pop();

            if(current_distance > distance[node]) {
                continue;
            }

            for (auto [next_node, weight] : graph[node]) {
                int new_distance = current_distance + weight;
                if (new_distance < distance[next_node]) {
                    distance[next_node] = new_distance;
                    min_heap.push({new_distance, next_node});
                }
            }
        }
        return distance;
    }

    int networkDelayTime(vector<vector<int>>& times, int n, int k) {
        std::vector<std::vector<std::pair<int, int>>> graph(n);
        for(const auto& edge : times) {
            graph[edge[0] - 1].push_back({edge[1] - 1, edge[2]});
        }
        auto distances = dijkstra(k - 1, graph);
        int maximum_distance = 0;
        for (auto distance : distances) {
            if (distance == INF) {return -1;}
            maximum_distance = std::max(maximum_distance, distance);
        }
        return maximum_distance;
    }
};
```

如果不仅需要记录最短路径长度，还需要具体的这条路径是什么，需要往里加一个parent来记录。

```cpp
class Solution {
public:
    using Edge = pair<int, int>;
    // {next_node, weight}

    using State = pair<int, int>;
    // {distance, node}

    pair<int, vector<int>> shortestPath(
        int start,
        int target,
        const vector<vector<Edge>>& graph
    ) {
        int n = static_cast<int>(graph.size());
        const int INF = numeric_limits<int>::max();

        vector<int> distance(n, INF);
        vector<int> parent(n, -1);

        priority_queue<
            State,
            vector<State>,
            greater<State>
        > min_heap;

        distance[start] = 0;
        min_heap.push({0, start});

        while (!min_heap.empty()) {
            auto [current_distance, node] = min_heap.top();
            min_heap.pop();

            if (current_distance > distance[node]) {
                continue;
            }

            // target 第一次以有效状态出堆，
            // 它的最短距离已经确定。
            if (node == target) {
                break;
            }

            for (const auto& [next_node, weight] : graph[node]) {
                int new_distance =
                    current_distance + weight;

                if (new_distance < distance[next_node]) {
                    distance[next_node] = new_distance;

                    // 记录 next_node 是从 node 到达的
                    parent[next_node] = node;

                    min_heap.push({
                        new_distance,
                        next_node
                    });
                }
            }
        }

        if (distance[target] == INF) {
            return {-1, {}};
        }

        vector<int> path;

        // 从终点沿 parent 倒推到起点
        for (int node = target;
             node != -1;
             node = parent[node]) {
            path.push_back(node);
        }

        // 当前是 target -> ... -> start，需要反转
        reverse(path.begin(), path.end());

        return {distance[target], path};
    }
};
```

如果涉及到多条路径还需要，还需要在求解路径的时候用DFS找出所有路径。

```cpp
// parents的定义变更如下
vector<vector<int>> parents(n);

// 更新的部分需要在距离相等的时候，将当前节点添加为父节点
if (new_distance < distance[next_node]) {
    distance[next_node] = new_distance;

    parents[next_node].clear();
    parents[next_node].push_back(node);

    min_heap.push({
        new_distance,
        next_node
    });
} else if (new_distance == distance[next_node]) {
    parents[next_node].push_back(node);
}

// 最后计算路径的时候需要用dfs向前回溯
void buildPaths(
    int node,
    int start,
    const vector<vector<int>>& parents,
    vector<int>& current_path,
    vector<vector<int>>& result
) {
    current_path.push_back(node);

    if (node == start) {
        vector<int> path(
            current_path.rbegin(),
            current_path.rend()
        );

        result.push_back(path);
    } else {
        for (int previous : parents[node]) {
            buildPaths(
                previous,
                start,
                parents,
                current_path,
                result
            );
        }
    }

    current_path.pop_back();
}
```

### 一般Dijkstra无法解决的最短路径问题

[787. Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/description/)，除了要求边权和小，还有轮数限制，用一般的Dijkstra算法就无法解决，因为可能存在这样的情况：

```text
到达 A：

路径一：价格 100，用 3 条边
路径二：价格 150，只用了 1 条边
```

用Dijkstra会选到价格100的路径，但它的边条数超过了限制，不满足要求。这种有额外限制的最短路径问题一般需要使用Bellman-Ford动态规划。

```cpp
class Solution {
public:
    int findCheapestPrice(
        int n,
        vector<vector<int>>& flights,
        int src,
        int dst,
        int k
    ) {
        const int INF = numeric_limits<int>::max();

        vector<int> distance(n, INF);
        distance[src] = 0;

        // 最多 K 个中转站，即最多使用 K + 1 条边
        for (int edges = 0; edges <= k; ++edges) {
            // 必须复制上一轮结果
            vector<int> next_distance = distance;

            for (const auto& flight : flights) {
                int from = flight[0];
                int to = flight[1];
                int price = flight[2];

                if (distance[from] == INF) {
                    continue;
                }

                next_distance[to] = min(
                    next_distance[to],
                    distance[from] + price
                );
            }

            distance = std::move(next_distance);
        }

        return distance[dst] == INF
            ? -1
            : distance[dst];
    }
};
```

如果一定要用Dijkstra算法，需要把边作为一个状态存入优先队列，上题的另一种解法如下：

```cpp
class Solution {
public:
    struct State {
        int cost;
        int node;
        int edges;

        bool operator>(const State& other) const {
            return cost > other.cost;
        }
    };

    int findCheapestPrice(
        int n,
        vector<vector<int>>& flights,
        int src,
        int dst,
        int k
    ) {
        vector<vector<pair<int, int>>> graph(n);

        for (const auto& flight : flights) {
            int from = flight[0];
            int to = flight[1];
            int price = flight[2];

            graph[from].push_back({to, price});
        }

        int max_edges = k + 1;
        const int INF = numeric_limits<int>::max();

        // distance[node][edges]:
        // 恰好使用 edges 条边到达 node 的最低价格
        vector<vector<int>> distance(
            n,
            vector<int>(max_edges + 1, INF)
        );

        priority_queue<
            State,
            vector<State>,
            greater<State>
        > min_heap;

        distance[src][0] = 0;
        min_heap.push({0, src, 0});

        while (!min_heap.empty()) {
            auto [cost, node, edges] = min_heap.top();
            min_heap.pop();

            if (cost > distance[node][edges]) {
                continue;
            }

            if (node == dst) {
                return cost;
            }

            if (edges == max_edges) {
                continue;
            }

            for (const auto& [next_node, price] : graph[node]) {
                int new_cost = cost + price;
                int new_edges = edges + 1;

                if (new_cost < distance[next_node][new_edges]) {
                    distance[next_node][new_edges] = new_cost;

                    min_heap.push({
                        new_cost,
                        next_node,
                        new_edges
                    });
                }
            }
        }

        return -1;
    }
};
```



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

## 二分查找 - Binary Search

二分查找是看起来简单、实则最容易写错的算法之一。ACM 赛场上"边界条件没写好导致死循环或漏解"几乎是最常见的 bug 之一——核心难点就在 mid 的计算方式和区间的开闭。本节整理三种最常考的二分模板。

### 标准库的三个函数

C++ STL 的 `<algorithm>` 提供了三个核心函数（要求区间已经排好序）：

- `std::binary_search(begin, end, value)`：判断 `value` 是否在区间内，返回 `bool`，时间复杂度 `O(log n)`。
- `std::lower_bound(begin, end, value)`：返回指向第一个**大于等于** `value` 的元素的迭代器；如果不存在，返回 `end`。
- `std::upper_bound(begin, end, value)`：返回指向第一个**严格大于** `value` 的元素的迭代器；如果不存在，返回 `end`。

### 手写二分模板

最容易记错的是 mid 的计算和边界收缩，建议背下面两个版本之一：

**版本一：闭区间 `[l, r]`，寻找 target**（target 存在时返回任一下标，不存在返回 -1）

```cpp
int binarySearch(const std::vector<int>& nums, int target) {
    int l = 0;
    int r = static_cast<int>(nums.size()) - 1;
    while (l <= r) {
        int mid = l + (r - l) / 2;  // 防止 (l+r) 整数相加溢出
        if (nums[mid] == target) {
            return mid;
        } else if (nums[mid] < target) {
            l = mid + 1;
        } else {
            r = mid - 1;
        }
    }
    return -1;
}
```

**版本二：在答案上二分**——找满足谓词 `predicate(x)` 的最小/最大 `x`，关键是 `predicate` 在定义域上**单调**（一段 false 后跟一段 true，或反过来）。

```cpp
// 寻找最小值 x 使得 predicate(x) == true
// 假设 predicate 在 [lo, hi] 上是 false ... false true ... true
int lowerBound(int lo, int hi) {
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (predicate(mid)) {
            hi = mid;        // mid 满足条件，答案在 [lo, mid]
        } else {
            lo = mid + 1;    // mid 不满足条件，答案在 [mid+1, hi]
        }
    }
    return lo;
}

// 寻找最大值 x 使得 predicate(x) == true
// 假设 predicate 在 [lo, hi] 上是 true ... true false ... false
int upperBound(int lo, int hi) {
    while (lo < hi) {
        int mid = lo + (hi - lo + 1) / 2;  // 向上取整，否则会死循环
        if (predicate(mid)) {
            lo = mid;        // mid 满足条件，答案在 [mid, hi]
        } else {
            hi = mid - 1;    // mid 不满足条件，答案在 [lo, mid-1]
        }
    }
    return lo;
}
```

记忆要点：
- `mid = lo + (hi - lo) / 2` 而不是 `(lo + hi) / 2` 是为了避免整数相加溢出。
- 找**最大**满足条件的时候，`mid` 要**向上取整**（`lo + (hi - lo + 1) / 2`），否则 `lo = mid` 不会前进，会死循环。
- 在答案上二分的核心套路是：**把"求最优"转化为"判定"**——给定一个候选答案，O(n) 或 O(n log n) 判断它是否可行，然后二分搜索最优解。

### 例题 1：寻找目标元素的第一个和最后一个位置

[LeetCode 34. Find First and Last Position of Element in Sorted Array](https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/)。这题是 `std::lower_bound` 和 `std::upper_bound` 的最佳应用：找到 `target` 第一次出现的位置，就是 `lower_bound(target)`；找到最后一次出现的位置，就是 `upper_bound(target) - 1`。如果两者相等，说明 `target` 不存在。

C++ 实现：

```cpp
class Solution {
public:
    std::vector<int> searchRange(
        std::vector<int>& nums,
        int target
    ) {
        auto lower = std::lower_bound(
            nums.begin(), nums.end(), target
        );
        auto upper = std::upper_bound(
            nums.begin(), nums.end(), target
        );

        if (lower == upper) {
            return {-1, -1};
        }

        return {
            static_cast<int>(lower - nums.begin()),
            static_cast<int>(upper - nums.begin() - 1)
        };
    }
};
```

Python 实现（`bisect_left` 和 `bisect_right` 分别对应 `lower_bound` 和 `upper_bound`，两者的差就是 `target` 的出现次数）：

```python
from typing import List
from bisect import bisect_left, bisect_right

class Solution:
    def searchRange(self, nums: List[int], target: int) -> List[int]:
        lower = bisect.bisect_left(nums, target)
        upper = bisect.bisect_right(nums, target)
        if lower == upper:
            return [-1, -1]
        
        return [lower, upper -1]
```

### 例题 2：在答案上二分

[LeetCode 410. Split Array Largest Sum](https://leetcode.com/problems/split-array-largest-sum/)。这题需要把一个数组分成 `m` 段，让最大的子段和最小。答案是"最大子段和"的最小值，典型的在答案上二分的题目。

我们可以把问题转化为一个判定问题：给定一个最大子段和 `limit`，能不能把数组分成不超过 `m` 段，使得每段的和都不超过 `limit`？这个判定函数是 `O(n)` 的贪心扫描，而 `limit` 的范围是 `[max(nums), sum(nums)]`。对 `limit` 做二分，总复杂度为 `O(n log(sum))`。

C++ 实现：

```cpp
class Solution {
public:
    // 给定 limit，能否把 nums 分成不超过 m 段使得每段和 <= limit
    bool canSplit(
        const std::vector<int>& nums,
        int m,
        long long limit
    ) {
        int pieces = 1;
        long long current = 0;
        for (int num : nums) {
            if (current + num <= limit) {
                current += num;
            } else {
                pieces++;
                current = num;
                if (pieces > m) {
                    return false;
                }
            }
        }
        return true;
    }

    int splitArray(
        std::vector<int>& nums,
        int m
    ) {
        long long lo = *std::max_element(
            nums.begin(), nums.end()
        );
        long long hi = std::accumulate(
            nums.begin(), nums.end(), 0LL
        );

        // 寻找最小值 x 使得 canSplit(..., x) == true
        // canSplit 在 x 上单调：x 越大越容易满足
        while (lo < hi) {
            long long mid = lo + (hi - lo) / 2;
            if (canSplit(nums, m, mid)) {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        return static_cast<int>(lo);
    }
};
```

Python 实现（请自行完成——提示：用 `max(nums)` 作为下界，`sum(nums)` 作为上界，谓词函数写成贪心的 `can_split`，然后套用"在答案上二分"的模板）：

```python
from typing import List


class Solution:
    def splitArray(self, nums: List[int], m: int) -> int:
        # TODO: 请实现"在答案上二分"的 splitArray
        # 1) 写一个 can_split(limit) 函数
        # 2) 对 [max(nums), sum(nums)] 二分
        pass
```

## 并查集 - Union-Find / DSU

并查集（Disjoint Set Union）是 ACM 比赛中最容易**写不出**的数据结构之一——核心代码只有十几行，但如果没有背下"路径压缩 + 按秩合并"两个优化，临场大概率会写错或者写出退化到 `O(n)` 的版本。它主要用于**处理元素的分组关系**和**判断两个元素是否属于同一组**——典型场景包括：图中的连通分量、岛屿问题、生成树相关（Kruskal）、冗余边检测等。

### 核心数据结构

并查集维护一个森林，每个集合用一棵树表示，根节点是这个集合的"代表"。需要三个关键的状态：

- `parent[i]`：节点 `i` 的父节点（根节点的 `parent` 指向自身）。
- `rank[i]` 或 `size[i]`：以 `i` 为根的树的深度/大小，用于**按秩合并**。
- 任意一个"非根"节点都可以通过 `find` 操作回到根。

### 三个基础操作

- `find(x)`：找到 `x` 所在集合的根，**同时把路径上所有节点直接挂到根上**（路径压缩）。
- `union(x, y)`：合并 `x` 和 `y` 所在的集合。先 `find` 出各自的根，再把秩/大小更小的根挂到更大的根下面（按秩合并）。
- `connected(x, y)`：等价于 `find(x) == find(y)`。

记忆要点：

1. `find` 必须**带路径压缩**，否则树可能退化成链，时间复杂度退化到 `O(n)`。写法是先递归找根，再把 `parent[x]` 指向根——`return parent[x] = find(parent[x])`。
2. `union` 必须**按秩合并**：两棵树深度不同时，把深度小的树根指向深度大的树根；如果深度相同，新根的深度加 1。这样能保证树的高度是 `O(log n)`。
3. 路径压缩 + 按秩合并后，单次操作均摊复杂度为 `O(α(n))`，其中 `α` 是反阿克曼函数，实际使用中可以视为常数。

### 模板代码

```cpp
class DSU {
public:
    std::vector<int> parent;
    std::vector<int> rank_;

    DSU(int n) {
        parent.resize(n);
        rank_.assign(n, 0);
        for (int i = 0; i < n; ++i) {
            parent[i] = i;
        }
    }

    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);  // 路径压缩
        }
        return parent[x];
    }

    void unite(int x, int y) {
        int rx = find(x);
        int ry = find(y);
        if (rx == ry) {
            return;
        }
        // 按秩合并
        if (rank_[rx] < rank_[ry]) {
            std::swap(rx, ry);
        }
        parent[ry] = rx;
        if (rank_[rx] == rank_[ry]) {
            rank_[rx]++;
        }
    }

    bool connected(int x, int y) {
        return find(x) == find(y);
    }
};
```

### 例题 1：省份数量

[LeetCode 547. Number of Provinces](https://leetcode.com/problems/number-of-provinces/)。这题是并查集的最直接应用：给定城市之间的邻接矩阵，求连通分量的数量。遍历邻接矩阵，把每对相连的城市 `unite` 起来，最后统计有多少个节点的 `parent[i] == i`（即根的数量）。

C++ 实现：

```cpp
class DSU {
public:
    std::vector<int> parent;
    std::vector<int> rank_;

    DSU(int n) : parent(n), rank_(n, 0) {
        for (int i = 0; i < n; ++i) {
            parent[i] = i;
        }
    }

    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);
        }
        return parent[x];
    }

    void unite(int x, int y) {
        int rx = find(x);
        int ry = find(y);
        if (rx == ry) return;
        if (rank_[rx] < rank_[ry]) std::swap(rx, ry);
        parent[ry] = rx;
        if (rank_[rx] == rank_[ry]) rank_[rx]++;
    }
};

class Solution {
public:
    int findCircleNum(std::vector<std::vector<int>>& isConnected) {
        int n = isConnected.size();
        DSU dsu(n);
        for (int i = 0; i < n; ++i) {
            for (int j = i + 1; j < n; ++j) {
                if (isConnected[i][j] == 1) {
                    dsu.unite(i, j);
                }
            }
        }
        int provinces = 0;
        for (int i = 0; i < n; ++i) {
            if (dsu.find(i) == i) {
                provinces++;
            }
        }
        return provinces;
    }
};
```

Python 实现（请自行完成——提示：可以用 `list` 当 `parent`，或者直接用 Python 自带的字典记录父节点；记得在 `find` 时做路径压缩）：

```python
from typing import List


class DSU:
    def __init__(self, n: int):
        # TODO: 初始化 parent 和 rank_
        pass

    def find(self, x: int) -> int:
        # TODO: 带路径压缩的 find
        pass

    def unite(self, x: int, y: int) -> None:
        # TODO: 按秩合并
        pass


class Solution:
    def findCircleNum(self, isConnected: List[List[int]]) -> int:
        # TODO: 调用 DSU，统计根节点数量
        pass
```

### 例题 2：冗余连接

[LeetCode 684. Redundant Connection](https://leetcode.com/problems/redundant-connection/)。这题给一棵树加上一条边后形成了带环的图，要求找到这条多余的边。思路：依次尝试加入每条边，加入前如果发现两个节点已经连通（即 `find(x) == find(y)`），说明这条边会形成环，它就是要找的冗余边。

C++ 实现：

```cpp
class Solution {
public:
    std::vector<int> parent;
    std::vector<int> rank_;

    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);
        }
        return parent[x];
    }

    bool unite(int x, int y) {
        int rx = find(x);
        int ry = find(y);
        if (rx == ry) {
            return false;  // 已在同一集合
        }
        if (rank_[rx] < rank_[ry]) std::swap(rx, ry);
        parent[ry] = rx;
        if (rank_[rx] == rank_[ry]) rank_[rx]++;
        return true;
    }

    std::vector<int> findRedundantConnection(
        std::vector<std::vector<int>>& edges
    ) {
        int n = edges.size();
        parent.resize(n + 1);
        rank_.assign(n + 1, 0);
        for (int i = 0; i <= n; ++i) parent[i] = i;

        for (const auto& edge : edges) {
            if (!unite(edge[0], edge[1])) {
                return edge;  // 这条边会造成环
            }
        }
        return {};
    }
};
```

Python 实现（请自行完成——提示：`unite` 在加入一条边之前如果发现两个节点已连通，就返回这条边本身）：

```python
from typing import List


class Solution:
    def findRedundantConnection(self, edges: List[List[int]]) -> List[int]:
        # TODO:
        # 1) 实现一个轻量的 DSU（parent list + find + unite）
        # 2) 遍历 edges，第一次让 unite 返回 False 时返回当前边
        pass
```
```

