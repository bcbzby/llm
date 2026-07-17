import type { QuestionOption } from '../types';

interface QuestionCardProps {
  content: string;
  questionType: string;
  options: QuestionOption[];
  selectedKeys: string[];
  onSelect: (keys: string[]) => void;
  showResult?: boolean;
  correctKeys?: string[];
  explanation?: string | null;
  isMarked?: boolean;
  onMark?: () => void;
}

export default function QuestionCard({
  content,
  questionType,
  options,
  selectedKeys,
  onSelect,
  showResult = false,
  correctKeys = [],
  explanation,
  isMarked,
  onMark,
}: QuestionCardProps) {
  const isMulti = questionType === 'multi_choice';

  const handleOptionClick = (key: string) => {
    if (showResult) return;
    if (isMulti) {
      const newKeys = selectedKeys.includes(key)
        ? selectedKeys.filter((k) => k !== key)
        : [...selectedKeys, key];
      onSelect(newKeys);
    } else {
      onSelect([key]);
    }
  };

  const getOptionStyle = (key: string) => {
    const isSelected = selectedKeys.includes(key);
    const isCorrect = correctKeys.includes(key);
    const isWrong = isSelected && !isCorrect;

    if (!showResult) {
      return isSelected
        ? 'border-blue-500 bg-blue-50 text-blue-700'
        : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50';
    }

    if (isCorrect && isSelected) return 'border-green-500 bg-green-50 text-green-700';
    if (isCorrect) return 'border-green-500 bg-green-50/50 text-green-600';
    if (isWrong) return 'border-red-500 bg-red-50 text-red-700';
    return 'border-gray-200 text-gray-500';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* 题目头部 */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <span className={`px-3 py-1 text-xs font-medium rounded-full ${
            questionType === 'multi_choice'
              ? 'bg-purple-100 text-purple-700'
              : 'bg-blue-100 text-blue-700'
          }`}>
            {questionType === 'multi_choice' ? '多选题' : '单选题'}
          </span>
          {onMark && (
            <button
              onClick={onMark}
              className={`px-3 py-1 text-xs rounded-full ${
                isMarked
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
              }`}
            >
              {isMarked ? '★ 已标记' : '☆ 标记回顾'}
            </button>
          )}
        </div>
        <p className="text-lg text-gray-900 leading-relaxed">{content}</p>
      </div>

      {/* 选项列表 */}
      <div className="p-6 space-y-3">
        {options.map((opt) => (
          <button
            key={opt.key}
            onClick={() => handleOptionClick(opt.key)}
            className={`w-full flex items-center p-4 rounded-lg border-2 transition-all duration-200 text-left ${getOptionStyle(opt.key)}`}
          >
            <span className={`flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full font-medium text-sm mr-3 ${
              selectedKeys.includes(opt.key)
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600'
            }`}>
              {opt.key}
            </span>
            <span className="text-base">{opt.content}</span>
            {showResult && correctKeys.includes(opt.key) && (
              <span className="ml-auto text-green-500">✓</span>
            )}
            {showResult && selectedKeys.includes(opt.key) && !correctKeys.includes(opt.key) && (
              <span className="ml-auto text-red-500">✗</span>
            )}
          </button>
        ))}
      </div>

      {/* 解析 */}
      {showResult && explanation && (
        <div className="px-6 pb-6">
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
            <p className="text-sm font-medium text-blue-800 mb-1">💡 解析</p>
            <p className="text-sm text-blue-700 whitespace-pre-line">{explanation}</p>
          </div>
        </div>
      )}
    </div>
  );
}
