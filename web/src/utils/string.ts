
/**
 * 获取用户名缩写（适合头像显示）
 * @param {string} name 用户名，例如 "nie chao"
 * @returns {string} 缩写，例如 "NC"
 */
export function getInitials(name: string) {
  if (!name) return "";

  const parts = name
    .trim()
    .split(/\s+/) // 按空格拆分
    .filter(Boolean);

  if (parts.length === 0) return "";

  // 多于两个词时，只取前两个
  return parts
    .slice(0, 2)
    .map(word => word[0].toUpperCase())
    .join("");
}
