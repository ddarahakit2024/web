export function filterPosts(posts, category, searchTerm) {
  const term = searchTerm.trim().toLocaleLowerCase()

  return posts.filter((post) => {
    const matchesCategory = category === '추천' || post.category === category
    const searchableText = `${post.title} ${post.place} ${post.excerpt} ${post.author}`.toLocaleLowerCase()
    return matchesCategory && (!term || searchableText.includes(term))
  })
}
