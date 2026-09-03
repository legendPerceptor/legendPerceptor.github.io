---
title: 2026 Hackathon复盘
date: 2026-08-29 08:43:00 +0800
categories: [Tutorial]
tags: [algorithm, C++, Python, 算法]
pin: false
math: true
---

> 复盘凭借印象构造题目大意后重新编写代码解题，使用的函数名和类名与比赛不同，主要提供算法和解题思路。我vibe code了一套评测机制，下面提到的解法也都放在了同一个repo里，想要练习的朋友可以从[Hackathon 26 Review Github Repo](https://github.com/legendPerceptor/hackathon-26-review)获取完整工程。
{: .prompt-tip }

## 第一题

**题目**：给定一个$m \times n$的矩阵，矩阵里的数都是非负整数，构造由同心正方形堆叠而成的乘积靶，最中心的一个正方形的乘积数是$k$，第二个$3 \times 3$的正方形的乘积数是$k-1$，第三个$5 \times 5$的正方形乘积数是$k-2$，以此类推，最大的一个正方形的乘积数是1。把这个乘积靶放在矩阵中，矩阵对应位置的元素和乘积靶的乘积数相乘求和，得到一个结果result，问对每个给定的矩阵，这个结果result最大是多少？

### 基本解题思路

这个result可以拆成$k$个同心全1的正方形相加，有

$$ result(i,j) = \sum_{r=0}^{k-1} SquareSum(i-r, j-r, i+r, j+r) $$

用二维前缀和，每个正方形区域的和可以O(1)得到，因此每个位置需要O(k)。

二维前缀和的数组存储的元素定义如下：

$$ prefix[i+1][j+1] = \sum_{0 \leq x \leq i, 0 \leq y \leq j} matrix[x][y] $$

矩形区域 $[x1, x2] \times [y_1, y_2]$的元素和为 

$$ prefix[x_2+1][y_2+1] - prefix[x_1][y_2+1] - prefix[x_2 +1][y1] + prefix[x1][y1] $$

乘积靶的边长为$2k-1$，需要满足$2k-1 \leq m$和$2k-1 \leq n$，所以最大值是

$$ k_{max} = \lfloor \frac{min(m,n)+1}{2} \rfloor $$


**C++实现**:

```cpp
#include <bits/stdc++.h>
using namespace std;

long long maxTargetResult(const vector<vector<int>> &matrix) {
    int m = matrix.size();
    if (m == 0) {
        return 0;
    }
    int n = matrix[0].size();
    int k = (min(m, n) + 1) / 2;
    int targetSize = 2 * k - 1;

    vector<vector<long long>> prefix(m + 1, vector<long long>(n + 1, 0));
    for (int i = 0; i < m; ++i) {
        for (int j = 0; j < n; ++j) {
            prefix[i + 1][j + 1] = matrix[i][j] + prefix[i][j + 1] +
                                   prefix[i + 1][j] - prefix[i][j];
        }
    }
    auto rectangleSum = [&](int top, int left, int bottom,
                            int right) -> long long {
        return prefix[bottom + 1][right + 1] - prefix[top][right + 1] -
               prefix[bottom + 1][left] + prefix[top][left];
    };
    long long answer = 0;
    // 枚举最大乘积靶的左上角
    // 靶覆盖:
    // [top, top + targetSize - 1]
    // [left, left + targetSize - 1]
    for (int top = 0; top + targetSize <= m; ++top) {
        for (int left = 0; left + targetSize <= n; ++left) {
            int centerRow = top + k - 1;
            int centerCol = left + k - 1;
            long long result = 0;
            for (int radius = 0; radius < k; ++radius) {
                result += rectangleSum(centerRow - radius, centerCol - radius,
                                       centerRow + radius, centerCol + radius);
            }
            answer = max(answer, result);
        }
    }
    return answer;
}
```

### 解法二：二阶差分 + 对角线前缀和

上面的做法对每个中心枚举一次半径。实际上可以把乘积靶看成一个二维卷积核：

$$ W(x,y)=k-\max(|x|,|y|),\qquad |x|,|y|<k $$

设靶心放在 $(i,j)$ 时的答案为 $F(i,j)$，矩阵外的元素都视为0。对水平方向做二阶差分：

$$ D(i,j)=F(i,j+1)-2F(i,j)+F(i,j-1) $$

固定 $x$ 后，$W(x,y)$ 关于 $y$ 是一段“平台加斜坡”。二阶差分后，整段区间内部都变成0，只在 `y=-k,-|x|,|x|,k` 四个位置非零。因此令 $r=k-1$，可以得到

$$
\begin{aligned}
D(i,j)= {}& \sum_{x=-r}^{r} A(i+x,j-k)
          + \sum_{x=-r}^{r} A(i+x,j+k) \\
         &- \sum_{x=-r}^{r} A(i+x,j+x)
          - \sum_{x=-r}^{r} A(i+x,j-x).
\end{aligned}
$$

右边分别是两条竖直线段和两条对角线段。预处理列前缀和、主对角线前缀和与副对角线前缀和后，$D(i,j)$ 可以在 $O(1)$ 时间算出。

接下来从矩阵左侧之外开始，利用

$$ F(i,j+1)=D(i,j)+2F(i,j)-F(i,j-1) $$

依次恢复这一行所有位置的结果。由于核的水平半径为 $k-1$，有 $F(i,-k-1)=F(i,-k)=0$，所以递推的初值也是已知的。整个算法只扫描常数次矩阵，时间复杂度为 $O(mn)$，与 $k$ 无关；空间复杂度为 $O(mn)$。

```cpp
#include <bits/stdc++.h>
using namespace std;

long long maxTargetResult2(const vector<vector<int>>& matrix) {
    int m = static_cast<int>(matrix.size());
    if (m == 0 || matrix[0].empty()) {
        return 0;
    }
    int n = static_cast<int>(matrix[0].size());
    int k = (min(m, n) + 1) / 2;
    int radius = k - 1;

    // column[i + 1][j]: 第j列前i个元素的和
    vector<vector<long long>> column(m + 1, vector<long long>(n));
    // diagonal[i + 1][j + 1]: 从左上方向走到(i,j)的前缀和
    vector<vector<long long>> diagonal(m + 1,
                                       vector<long long>(n + 1));
    // antiDiagonal[i + 1][j]: 从右上方向走到(i,j)的前缀和
    vector<vector<long long>> antiDiagonal(m + 1,
                                           vector<long long>(n + 1));

    for (int i = 0; i < m; ++i) {
        for (int j = 0; j < n; ++j) {
            column[i + 1][j] = column[i][j] + matrix[i][j];
            diagonal[i + 1][j + 1] = diagonal[i][j] + matrix[i][j];
        }
        for (int j = n - 1; j >= 0; --j) {
            antiDiagonal[i + 1][j] =
                antiDiagonal[i][j + 1] + matrix[i][j];
        }
    }

    auto columnSum = [&](int centerRow, int col) -> long long {
        if (col < 0 || col >= n) {
            return 0;
        }
        int top = max(0, centerRow - radius);
        int bottom = min(m - 1, centerRow + radius);
        return column[bottom + 1][col] - column[top][col];
    };

    // 求 sum matrix[centerRow+t][centerCol+direction*t]。
    // direction=1 是主对角线，direction=-1 是副对角线。
    auto diagonalSum = [&](int centerRow, int centerCol,
                           int direction) -> long long {
        int low = max(-radius, -centerRow);
        int high = min(radius, m - 1 - centerRow);
        if (direction == 1) {
            low = max(low, -centerCol);
            high = min(high, n - 1 - centerCol);
        } else {
            low = max(low, centerCol - (n - 1));
            high = min(high, centerCol);
        }
        if (low > high) {
            return 0;
        }

        int topRow = centerRow + low;
        int topCol = centerCol + direction * low;
        int bottomRow = centerRow + high;
        int bottomCol = centerCol + direction * high;

        if (direction == 1) {
            return diagonal[bottomRow + 1][bottomCol + 1] -
                   diagonal[topRow][topCol];
        }
        return antiDiagonal[bottomRow + 1][bottomCol] -
               antiDiagonal[topRow][topCol + 1];
    };

    long long answer = 0;
    // 只枚举能完整放下乘积靶的行。
    for (int i = radius; i + radius < m; ++i) {
        long long previous = 0;  // F(i, -k-1)
        long long current = 0;   // F(i, -k)

        // 用D(i,j)算出F(i,j+1)，直到恢复到最后一个合法中心。
        for (int j = -k; j < n - radius - 1; ++j) {
            long long difference =
                columnSum(i, j - k) + columnSum(i, j + k) -
                diagonalSum(i, j, 1) - diagonalSum(i, j, -1);
            long long next = difference + 2 * current - previous;
            previous = current;
            current = next;

            int centerCol = j + 1;
            if (centerCol >= radius) {
                answer = max(answer, current);
            }
        }
    }
    return answer;
}
```

## 第二题

**题目**：给定一个数组array，长度为n，n一定是偶数，你和机器人比赛，每轮你先拿走数组中任意一个数，机器人总是会选择剩下的数组中间那个数，问你最高得分能到多少？

**解题思路:**

首先这题不是直接拿最大值，对一个数组`[0,1,0,2]`，如果拿了最大值2，机器人拿1，剩下只能拿0，总分2分，但如果先拿1，机器人会拿0，之后可以拿2，总得分为3分。

这题的思路是把数组分成两半，机器人在每一轮一定是拿中间的2个元素之一，每轮把中间两个元素放入优先队列，让机器人拿最小的那个，算出的分就是机器人最小得分，用总和减去机器人的最小得分就是我能获得的最高分。

**C++实现**:

```cpp
#include <bits/stdc++.h>
using namespace std;

long long maxScore(const vector<int>& array) {
    int n = array.size();

    long long totalSum = std::accumulate(array.begin(), array.end(), 0LL);

    priority_queue<int, vector<int>, greater<int>> minHeap;

    long long robotScore = 0;
    int left = n / 2 - 1;
    int right = n / 2;
    while (left >= 0) {
        minHeap.push(array[left]);
        minHeap.push(array[right]);
        robotScore += minHeap.top();
        minHeap.pop();
        --left;
        ++right;
    }
    return totalSum - robotScore;
}
```

## 第三题

**题目**:给定一个$m \times n$的网格，在$(x1,y1)$, $(x2, y2)$放置两台监视器，第一台监视器可以覆盖 `[x1, x1 + scope]`的纵向无限长区间，第二台监视器可以覆盖`[y2, y2 + scope]`的横向无限长区间。现在给定一个pos数组，包含生物栖息地所在的坐标，问当选取最优的监视器放置策略时，最多能覆盖多少个栖息地？

### **解法一**： 时间复杂度 $O(k^2)$，k为pos数组的长度。

> 该解法会超时，主要在于内层循环还需要遍历所有点，如果把找第二个监视器覆盖剩余点的问题优化成 $\log k$，就能得到最优解。
{: .prompt-danger }

先固定一台监视器的竖直区间，对于没有被第一台覆盖的点，再选择一个长度为scope的y区间，让第二台覆盖尽可能多的点。

最优区间的左端点一定可以放在某个栖息地的x或y坐标上，对第一台只需要枚举`pos[i].x`，对第二台枚举`pos[i].y`。

```cpp
#include <bits/stdc++.h>
using namespace std;

int maxCoveredHabitats(const vector<pair<int, int>>& pos, int scope) {
    int k = static_cast<int>(pos.size());
    int answer = 0;

    for (int j = 0; j < k; j++) {
        int yStart = pos[j].second;
        int covered = 0;

        for (const auto& [x, y] : pos) {
            if (yStart <= y && y <= yStart + scope) {
                ++covered;
            }
        }
        answer = max(answer, covered);
    }

    for (int i = 0; i < k; ++i) {
        int xStart = pos[i].first;
        int verticalCovered = 0;

        vector<int> remainingY;

        for (const auto& [x, y] : pos) {
            if (xStart <= x && x <= xStart + scope) {
                ++verticalCovered;
            } else {
                remainingY.push_back(y);
            }
        }

        sort(remainingY.begin(), remainingY.end());

        int left = 0;
        for (int right = 0; right < static_cast<int>(remainingY.size());
             ++right) {
            while (remainingY[right] - remainingY[left] > scope) {
                ++left;
            }
            int horizontalCovered = right - left + 1;
            answer = max(answer, verticalCovered + horizontalCovered);
        }
        answer = max(answer, verticalCovered);
    }
    return answer;
}
```

### **解法二**：扫描线+线段树，当k达到10^5时得用这种优化解法，时间复杂度为$O(k \log k)$。

思路如下：
1. 按x排序，使用滑动窗口维护第一台监视器当前覆盖的点。
2. 对于第一台没有覆盖的点，维护第二台监视器在不同$y_2$下能覆盖多少个点。
3. 一个纵坐标为y的点，可以被所有满足 $y-scope \leq y_2 \leq y$ 的水平区间覆盖。
4. 将所有可能的$y_2$离散化，用线段树维护区间加法和全局最大值。
5. 一个点进入第一台监视器时，将它从第二台的统计中删除，离开时再加回来。

```cpp
#include <bits/stdc++.h>
using namespace std;

class SegmentTree {
private:
    int n;
    vector<int> maximum;
    vector<int> lazy;

    void apply(int node, int value) {
        maximum[node] += value;
        lazy[node] += value;
    }

    void pushDown(int node) {
        if (lazy[node] == 0) {
            return;
        }

        apply(node * 2, lazy[node]);
        apply(node * 2 + 1, lazy[node]);
        lazy[node] = 0;
    }

    void rangeAdd(int node, int left, int right, int queryLeft, int queryRight,
                  int value) {
        if (queryLeft <= left && right <= queryRight) {
            apply(node, value);
            return;
        }
        pushDown(node);
        int middle = left + (right - left) / 2;
        if (queryLeft <= middle) {
            rangeAdd(node * 2, left, middle, queryLeft, queryRight, value);
        }
        if (queryRight > middle) {
            rangeAdd(node * 2 + 1, middle + 1, right, queryLeft, queryRight,
                     value);
        }
        maximum[node] = max(maximum[node * 2], maximum[node * 2 + 1]);
    }

public:
    explicit SegmentTree(int size)
        : n(size), maximum(size * 4, 0), lazy(size * 4, 0) {}
    void rangeAdd(int left, int right, int value) {
        if (left > right || n == 0) {
            return;
        }
        rangeAdd(1, 0, n - 1, left, right, value);
    }
    int getMaximum() const { return n == 0 ? 0 : maximum[1]; }
};

int maxCoveredHabitats(const vector<pair<int, int>>& inputPoints, int scope) {
    vector<pair<int, int>> points = inputPoints;
    int k = static_cast<int>(points.size());
    if (k == 0) {
        return 0;
    }
    sort(points.begin(), points.end());
    // candidates维护第二台水平监视器所有值得考虑的起始纵坐标
    vector<long long> candidates;
    for (const auto& [x, y] : points) {
        candidates.push_back(y);
    }
    sort(candidates.begin(), candidates.end());
    candidates.erase(unique(candidates.begin(), candidates.end()),
                     candidates.end());
    // 线段树维护对于每一个候选水平区间起点
    // y_2，第二台监视器当前能够覆盖多少个“没有被第一台监视器覆盖”的栖息地。
    SegmentTree tree(static_cast<int>(candidates.size()));

    auto updatePoint = [&](long long y, int delta) {
        int left = static_cast<int>(
            lower_bound(candidates.begin(), candidates.end(), y - scope) -
            candidates.begin());
        int right = static_cast<int>(
                        upper_bound(candidates.begin(), candidates.end(), y) -
                        candidates.begin()) -
                    1;
        tree.rangeAdd(left, right, delta);
    };

    // 初始状态：所有点都不在监视器1中，都放在第二台监视器里统计
    for (const auto& [x, y] : points) {
        updatePoint(y, 1);
    }

    int answer = tree.getMaximum();
    int right = 0;
    int verticalCovered = 0;

    // 按照相同 x 分组枚举第一台监视器的左端点。
    int left = 0;
    while (left < k) {
        long long xStart = points[left].first;

        // 被第一台监视器维护了的点，要从第二台里减掉
        while (right < k && points[right].first <= xStart + scope) {
            updatePoint(points[right].second, -1);
            ++verticalCovered;
            ++right;
        }

        answer = max(answer, verticalCovered + tree.getMaximum());

        int nextLeft = left;
        // 第一台监视器往前走，要在第二台里把nextLeft之前的加回来
        while (nextLeft < k && points[nextLeft].first == xStart) {
            updatePoint(points[nextLeft].second, 1);
            --verticalCovered;
            ++nextLeft;
        }
        left = nextLeft;
    }
    return answer;
}
```


## 第四题

**题目**: 总共有$n$个节点。有一个数组$s$，每个元素$s[i]$包含一个二元组$(u, v)$表示从节点$u$到节点$v$之间的边。再给定第二个整数数组$p$，长度和$s$一样，表示$s$中每条边所属的组号$g$。接下来有一个queries数组，每个query包含一个二元组$(g1, g2)$，表示query选取的两组边，针对query选择的两组边构建无向图，求每个query对应无向图的连通数（即形成了几个岛屿）。

### 解法一：基础思路
1. 按组把边分类存到一个unordered_map里，可以用组号获得所有该组的边。
2. 每轮query创建新的并查集，初始连通数为n。
3. 遍历query里要求的两组边，进行unite操作，完成后即获得最终连通数。

> TLE警告：由于s和queries.size()达到1e5，这个方案会超时。这题主要就难在这个点，该方案也能有97%的用例通过，可惜没有部分分。
{: .prompt-danger }

```cpp
#include <bits/stdc++.h>
using namespace std;

class DSU {
private:
    vector<int> parent;
    vector<int> size;
    int componentCount;

public:
    explicit DSU(int n) : parent(n), size(n, 1), componentCount(n) {
        std::iota(parent.begin(), parent.end(), 0);
    }
    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);
        }
        return parent[x];
    }
    bool unite(int x, int y) {
        int rootX = find(x);
        int rootY = find(y);
        if (rootX == rootY) {
            return false;
        }
        if (size[rootX] < size[rootY]) {
            swap(rootX, rootY);
        }
        parent[rootY] = rootX;
        size[rootX] += size[rootY];
        --componentCount;
        return true;
    }
    int count() const { return componentCount; }
};

vector<int> countComponents(int n, const vector<pair<int, int>>& s,
                            const vector<int>& p,
                            const vector<pair<int, int>>& queries) {
    unordered_map<int, vector<pair<int, int>>> groupEdges;

    for (size_t i = 0; i < s.size(); ++i) {
        groupEdges[p[i]].push_back(s[i]);
    }
    vector<int> answer;
    answer.reserve(queries.size());

    for (const auto& [g1, g2] : queries) {
        DSU dsu(n);
        auto it1 = groupEdges.find(g1);
        if (it1 != groupEdges.end()) {
            for (const auto& [u, v] : it1->second) {
                dsu.unite(u, v);
            }
        }

        if (g2 != g1) {
            auto it2 = groupEdges.find(g2);
            if (it2 != groupEdges.end()) {
                for (const auto& [u, v] : it2->second) {
                    dsu.unite(u, v);
                }
            }
        }
        answer.push_back(dsu.count());
    }
    return answer;
}
```

### 解法二：根号分治+可回滚并查集

这题赛场上没能过，赛后想了想根号分治+可回滚并查集应该能解决，太复杂了，不熟悉现场来不及写。

分治的重点问题在于大组的边很多，不能在每个query中重复加入；小组虽然重复加入，但每组边数不超过阈值B，所以单次成本可控。m为边数，n为节点数，取$ B=\sqrt{m} $，当$m=10^5$,重组数量最多只有316个，不同的重组+重组组合最多为$316 \times 315 / 2 \approx 50000$。通过分治的策略，让最坏复杂度大约为

$$ O(\frac{m^2}{B} \log n) = O(m \sqrt{m} \log n) $$

**可回滚并查集**： 普通的并查集使用路径压缩后，很难撤销。可回滚并查集：(1)不使用路径压缩; (2)使用按大小合并，保证树高度为$O(\log n)$; (3)每次合并记录修改；(4)可以回到之前的快照。这样处理一对组时，可以记录快照，临时加入第二组边，得到连通分量数，回滚到快照。

**C++实现**：

```cpp
class RollbackDSU {
private:
    struct Change {
        int childRoot;
        int parentRoot;
        int oldParentSize;
    };

    vector<int> parent;
    vector<int> treeSize;
    vector<Change> history;
    int componentCount;

public:
    explicit RollbackDSU(int n) : parent(n), treeSize(n, 1), componentCount(n) {
        iota(parent.begin(), parent.end(), 0);
    }

    // 回滚并查集不能路径压缩
    int find(int x) const {
        while (parent[x] != x) {
            x = parent[x];
        }
        return x;
    }

    bool unite(int x, int y) {
        int rootX = find(x);
        int rootY = find(y);

        if (rootX == rootY) {
            return false;
        }
        if (treeSize[rootX] < treeSize[rootY]) {
            swap(rootX, rootY);
        }
        history.push_back({rootY, rootX, treeSize[rootX]});
        parent[rootY] = rootX;
        treeSize[rootX] += treeSize[rootY];
        --componentCount;

        return true;
    }

    int snapshot() const { return static_cast<int>(history.size()); }

    void rollback(int snapshotSize) {
        while (static_cast<int>(history.size()) > snapshotSize) {
            Change change = history.back();
            history.pop_back();

            parent[change.childRoot] = change.childRoot;
            treeSize[change.parentRoot] = change.oldParentSize;
            ++componentCount;
        }
    }

    int count() const { return componentCount; }
};

using Edge = pair<int, int>;

struct PairHash {
    size_t operator()(const pair<int, int>& p) const {
        uint64_t first = static_cast<uint32_t>(p.first);
        uint64_t second = static_cast<uint32_t>(p.second);
        return static_cast<size_t>((first << 32) ^ second);
    }
};

static pair<int, int> normalizePair(int g1, int g2) {
    if (g1 > g2) {
        swap(g1, g2);
    }
    return {g1, g2};
}

static void addEdges(RollbackDSU& dsu, const vector<Edge>& edges) {
    for (const auto& [u, v] : edges) {
        dsu.unite(u, v);
    }
}

vector<int> countComponents(int n, const vector<pair<int, int>>& s,
                            const vector<int>& p,
                            const vector<pair<int, int>>& queries) {
    int m = static_cast<int>(s.size());
    int threshold = max(1, static_cast<int>(sqrt(max(1, m))) + 1);
    unordered_map<int, vector<Edge>> groupEdges;
    groupEdges.reserve(p.size() * 2);

    for (int i = 0; i < m; ++i) {
        groupEdges[p[i]].push_back(s[i]);
    }

    unordered_map<int, bool> isHeavy;
    isHeavy.reserve(groupEdges.size() * 2);

    for (const auto& [group, edges] : groupEdges) {
        isHeavy[group] = static_cast<int>(edges.size()) >= threshold;
    }

    vector<pair<int, int>> normalizedQueries;
    normalizedQueries.reserve(queries.size());
    unordered_map<pair<int, int>, int, PairHash> answer;
    answer.reserve(queries.size() * 2);

    for (const auto& [g1, g2] : queries) {
        auto key = normalizePair(g1, g2);
        normalizedQueries.push_back(key);
        answer.emplace(key, -1);
    }

    /*
     * 把待计算的查询分成两类：
     *
     * 1. 轻组 + 轻组
     * 2. 至少包含一个重组
     *
     * 第二类查询分配给其中一个重组。
     */
    vector<pair<int, int>> lightQueries;
    // heavyQueries[h] 表示以重组 h 作为基础的查询。
    unordered_map<int, vector<pair<int, int>>> heavyQueries;
    heavyQueries.reserve(groupEdges.size());

    for (const auto& [key, unused] : answer) {
        int g1 = key.first;
        int g2 = key.second;
        bool heavy1 = isHeavy.find(g1) != isHeavy.end() && isHeavy[g1];
        bool heavy2 = isHeavy.find(g2) != isHeavy.end() && isHeavy[g2];
        if (!heavy1 && !heavy2) {
            lightQueries.push_back(key);
        } else if (heavy1) {
            heavyQueries[g1].push_back(key);
        } else {
            heavyQueries[g2].push_back(key);
        }
    }

    RollbackDSU dsu(n);

    // 处理轻组+轻组
    for (const auto& key : lightQueries) {
        int snapshot = dsu.snapshot();
        int g1 = key.first;
        int g2 = key.second;
        auto it1 = groupEdges.find(g1);
        if (it1 != groupEdges.end()) {
            addEdges(dsu, it1->second);
        }
        if (g2 != g1) {
            auto it2 = groupEdges.find(g2);
            if (it2 != groupEdges.end()) {
                addEdges(dsu, it2->second);
            }
        }
        answer[key] = dsu.count();
        dsu.rollback(snapshot);
    }

    // 处理包含重组的查询
    for (const auto& [heavyGroup, queryList] : heavyQueries) {
        // 当前DSU应为空状态
        int emptySnapshot = dsu.snapshot();
        addEdges(dsu, groupEdges[heavyGroup]);
        int heavySnapshot = dsu.snapshot();

        for (const auto& key : queryList) {
            int otherGroup = key.first == heavyGroup ? key.second : key.first;

            if (otherGroup != heavyGroup) {
                auto it = groupEdges.find(otherGroup);
                if (it != groupEdges.end()) {
                    addEdges(dsu, it->second);
                }
            }

            answer[key] = dsu.count();
            dsu.rollback(heavySnapshot);
        }
        dsu.rollback(emptySnapshot);
    }
    // 按照原始查询顺序返回。
    vector<int> result;
    result.reserve(queries.size());

    for (const auto& key : normalizedQueries) {
        result.push_back(answer[key]);
    }

    return result;
}
```
### 解法三：不使用回滚并查集：基础重组 + 稀疏临时并查集

上面的可回滚并查集方案能够通过最大数据，但回滚并查集不能使用路径压缩，单次
`find` 的复杂度是 $O(\log n)$。还可以利用一个更直接的观察避免回滚：对于包含重组
$H$ 的查询，先只使用 $H$ 的边构建一个不会再修改的普通并查集；另一组 $G$ 的边
$(u,v)$ 实际连接的是两个基础连通块

$$ root_H(u),\ root_H(v) $$

因此，每个查询只需用一个临时并查集合并这些基础连通块。基础并查集不会被修改，
自然不需要快照和回滚，而且两个并查集都可以正常使用路径压缩。

仍令分组阈值 $B=\sqrt m$：

1. **轻组 + 轻组**：两组一共不超过 $2B$ 条边，直接放入临时并查集；
2. **重组 + 任意组**：相同重组的查询放在一起，建立一次基础并查集。针对每个查询，
   将另一组边的两个端点映射到基础并查集的根，再放进临时并查集；
3. 使用时间戳实现稀疏并查集。每次清空只需增加时间戳，只有本轮访问的节点才会被
   初始化，避免每个查询花费 $O(n)$ 重建数组；
4. 查询组对先标准化并去重，$(g_1,g_2)$ 与 $(g_2,g_1)$ 只计算一次。

设查询数为 $q$。轻查询最多扫描 $O(B)$ 条边；重查询的基础组只建立一次，另一组的
边仍按根号分治的方式扫描。总复杂度约为

$$
O\left(qB\alpha(n)+\frac{m^2}{B}\alpha(n)\right)
$$

取 $B=\sqrt m$，当 $q$ 与 $m$ 同阶时为

$$ O(m\sqrt m\alpha(n)) $$

这里的 $\alpha(n)$ 是普通路径压缩并查集的均摊复杂度。相比回滚版本的
$O(m\sqrt m\log n)$，它去掉了 `find` 的 $\log n$ 因子。实际运行时间的主要部分仍然
是扫描各组的边，所以常数级提升通常没有公式看起来那么大，但代码不再需要维护修改
历史，思路也更加直观。

BFS 或 DFS 并不能带来同样的优化。若针对每个查询重新遍历所选两组构成的图，最坏
仍需 $O(q(n+m))$；即使忽略孤立点，也会为大量查询反复扫描热门组的边。

下面是完整实现：

```cpp
namespace q4_v3 {

using Edge = pair<int, int>;

struct PairHash {
    size_t operator()(const pair<int, int>& value) const {
        uint64_t first = static_cast<uint32_t>(value.first);
        uint64_t second = static_cast<uint32_t>(value.second);
        return static_cast<size_t>((first << 32) ^ second);
    }
};

static pair<int, int> normalizePair(int first, int second) {
    if (first > second) swap(first, second);
    return {first, second};
}

class SparseDSU {
    vector<int> parent, treeSize, version;
    int currentVersion = 1;

    void activate(int node) {
        if (version[node] != currentVersion) {
            version[node] = currentVersion;
            parent[node] = node;
            treeSize[node] = 1;
        }
    }

public:
    explicit SparseDSU(int n) : parent(n), treeSize(n), version(n, 0) {}

    void reset() { ++currentVersion; }

    int find(int node) {
        activate(node);
        if (parent[node] != node) parent[node] = find(parent[node]);
        return parent[node];
    }

    bool unite(int first, int second) {
        int rootFirst = find(first), rootSecond = find(second);
        if (rootFirst == rootSecond) return false;
        if (treeSize[rootFirst] < treeSize[rootSecond]) swap(rootFirst, rootSecond);
        parent[rootSecond] = rootFirst;
        treeSize[rootFirst] += treeSize[rootSecond];
        return true;
    }
};

vector<int> countComponents(int n, const vector<Edge>& edges, const vector<int>& groups,
                            const vector<pair<int, int>>& queries) {
    int m = static_cast<int>(edges.size());
    int threshold = max(1, static_cast<int>(sqrt(max(1, m))) + 1);

    unordered_map<int, vector<Edge>> groupEdges;
    for (int i = 0; i < m; ++i) groupEdges[groups[i]].push_back(edges[i]);

    auto isHeavy = [&](int group) {
        auto it = groupEdges.find(group);
        return it != groupEdges.end() &&
               static_cast<int>(it->second.size()) >= threshold;
    };

    vector<pair<int, int>> normalizedQueries;
    unordered_map<pair<int, int>, int, PairHash> answers;
    for (auto [first, second] : queries) {
        auto key = normalizePair(first, second);
        normalizedQueries.push_back(key);
        answers.emplace(key, -1);
    }

    vector<pair<int, int>> lightQueries;
    unordered_map<int, vector<pair<int, int>>> heavyQueries;
    for (const auto& [key, unused] : answers) {
        bool firstHeavy = isHeavy(key.first);
        bool secondHeavy = isHeavy(key.second);
        if (!firstHeavy && !secondHeavy) {
            lightQueries.push_back(key);
        } else {
            heavyQueries[firstHeavy ? key.first : key.second].push_back(key);
        }
    }

    SparseDSU temporary(n);

    for (auto [first, second] : lightQueries) {
        temporary.reset();
        int components = n;
        auto addGroup = [&](int group) {
            auto it = groupEdges.find(group);
            if (it == groupEdges.end()) return;
            for (auto [u, v] : it->second) {
                if (temporary.unite(u, v)) --components;
            }
        };
        addGroup(first);
        if (second != first) addGroup(second);
        answers[{first, second}] = components;
    }

    SparseDSU base(n);

    for (const auto& [baseGroup, queryList] : heavyQueries) {
        base.reset();
        int baseComponents = n;
        for (auto [u, v] : groupEdges[baseGroup]) {
            if (base.unite(u, v)) --baseComponents;
        }

        for (const auto& key : queryList) {
            int otherGroup = key.first == baseGroup ? key.second : key.first;
            if (otherGroup == baseGroup) {
                answers[key] = baseComponents;
                continue;
            }

            temporary.reset();
            int components = baseComponents;
            auto it = groupEdges.find(otherGroup);
            if (it != groupEdges.end()) {
                for (auto [u, v] : it->second) {
                    int rootU = base.find(u), rootV = base.find(v);
                    if (temporary.unite(rootU, rootV)) --components;
                }
            }
            answers[key] = components;
        }
    }

    vector<int> result;
    result.reserve(queries.size());
    for (const auto& key : normalizedQueries) result.push_back(answers[key]);
    return result;
}

}  // namespace q4_v3
```
