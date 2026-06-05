// 模拟数据
export const mockOutlines = [
  {
    id: 'outline_001',
    topic: 'Python基础语法',
    subject: '编程',
    level: '入门',
    duration: 45,
    modules: [
      { id: 1, name: '变量与数据类型', duration: 10, difficulty: 'easy', keyPoints: ['变量定义', '数据类型', '类型转换'] },
      { id: 2, name: '条件语句', duration: 15, difficulty: 'medium', keyPoints: ['if语句', 'elif分支', '嵌套条件'] },
      { id: 3, name: '循环结构', duration: 20, difficulty: 'medium', keyPoints: ['for循环', 'while循环', 'break与continue'] }
    ]
  }
]

export const mockQuestions = [
  {
    id: 'q_001',
    type: 'choice',
    content: 'Python中以下哪个是正确的变量命名？',
    options: ['2name', 'my-name', 'my_name', 'class'],
    correctAnswer: 2,
    explanation: 'Python变量名不能以数字开头，不能包含连字符，不能使用关键字'
  },
  {
    id: 'q_002',
    type: 'choice',
    content: '以下哪个是Python的整数类型？',
    options: ['1.5', 'True', '42', '"hello"'],
    correctAnswer: 2,
    explanation: '整数类型用int表示，1.5是浮点数，True是布尔值，"hello"是字符串'
  },
  {
    id: 'q_003',
    type: 'fill',
    content: '将字符串"Hello"转换为大写应使用___方法',
    correctAnswer: 'upper',
    explanation: 'str.upper()方法可以将字符串中所有字符转换为大写'
  },
  {
    id: 'q_004',
    type: 'choice',
    content: 'Python中，用于输出内容到控制台的函数是？',
    options: ['input()', 'print()', 'echo()', 'console.log()'],
    correctAnswer: 1,
    explanation: 'print()是Python的标准输出函数，input()用于接收用户输入'
  }
]

export const mockStudyReport = {
  date: '2026-05-11',
  duration: 45,
  score: 88,
  xpEarned: 68,
  knowledgeRadar: {
    labels: ['变量类型', '条件判断', '循环结构', '函数调用', '列表操作'],
    data: [95, 82, 75, 88, 65]
  },
  questionsAnswered: 12,
  correctRate: 83,
  questionsCount: 5,
  strengths: ['对变量类型的理解比较扎实', '条件语句的逻辑清晰'],
  weaknesses: ['循环嵌套的运用还需加强', '列表操作不够熟练'],
  suggestions: ['建议加强循环结构的练习', '可以尝试做一些算法题目提升能力'],
  aiComments: '今天的课堂表现很棒！你展现了良好的学习状态，继续保持这个节奏！'
}

export const mockLeaderboard = [
  { rank: 1, nickname: '编程小王子', avatar: '👨‍💻', level: 28, xp: 15680, streak: 45, change: 0 },
  { rank: 2, nickname: 'AI学习狂人', avatar: '🤖', level: 25, xp: 14250, streak: 32, change: 2 },
  { rank: 3, nickname: '数据分析师', avatar: '📊', level: 24, xp: 13800, streak: 28, change: -1 },
  { rank: 4, nickname: '前端开发者', avatar: '🎨', level: 23, xp: 12500, streak: 21, change: 1 },
  { rank: 5, nickname: '算法爱好者', avatar: '🧮', level: 22, xp: 11900, streak: 18, change: -2 },
  { rank: 6, nickname: '后端新手', avatar: '⚙️', level: 21, xp: 11200, streak: 15, change: 0 },
  { rank: 7, nickname: '全栈梦想家', avatar: '🚀', level: 20, xp: 10500, streak: 12, change: 3 },
  { rank: 8, nickname: '技术宅', avatar: '🎮', level: 19, xp: 9800, streak: 10, change: -1 },
  { rank: 9, nickname: '代码诗人', avatar: '📝', level: 18, xp: 9200, streak: 8, change: 0 },
  { rank: 10, nickname: '学习机器', avatar: '🤓', level: 17, xp: 8600, streak: 7, change: 2 },
  { rank: 11, nickname: '你好世界', avatar: '🌍', level: 16, xp: 7200, streak: 5, change: 0 },
  { rank: 12, nickname: '学海无涯', avatar: '📚', level: 15, xp: 6500, streak: 4, change: 1 },
  { rank: 13, nickname: '初学者A', avatar: '🧑‍🎓', level: 14, xp: 5800, streak: 3, change: -1 },
  { rank: 14, nickname: '勤奋的小蜜蜂', avatar: '🐝', level: 13, xp: 5200, streak: 2, change: 0 },
  { rank: 15, nickname: '探索者', avatar: '🔭', level: 12, xp: 4500, streak: 1, change: 0 }
]

export const mockClassmates = [
  { id: 'cls_001', type: 'active', nickname: '小乐', avatar: '😎', expression: 'happy', status: 'online', isAnswering: false, lastAction: '✅ 答对了' },
  { id: 'cls_002', type: 'struggling', nickname: '小困', avatar: '😵', expression: 'confused', status: 'online', isAnswering: false, lastAction: '❌ 答错了' }
]

export const mockEggDrops = [
  { title: '知识彩蛋!', content: '你知道吗？Python的名字来源于 Monty Python 的马戏团，而不是那条蛇！', xp: 5 },
  { title: '编程趣闻', content: '第一版Python发布于1991年，比大多数人的父母年纪还大哦！', xp: 5 },
  { title: '小技巧', content: '使用 enumerate() 可以同时获取索引和值，比手动维护计数器更优雅！', xp: 5 }
]
