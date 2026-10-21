import { describe, expect, test } from '@jest/globals'
import { filterPosts } from './stores/postFilters.js'

const posts = [
  { title: '바다 산책', place: '제주 애월', excerpt: '파도 소리', author: '서윤', category: '바다' },
  { title: '도시의 밤', place: '부산 광안리', excerpt: '골목 풍경', author: '민호', category: '도시 산책' },
]

describe('filterPosts', () => {
  test('추천 카테고리에서 모든 게시글을 보여준다', () => {
    expect(filterPosts(posts, '추천', '')).toHaveLength(2)
  })

  test('선택한 카테고리에 해당하는 게시글만 보여준다', () => {
    expect(filterPosts(posts, '바다', '').map((post) => post.title)).toEqual(['바다 산책'])
  })

  test('검색어 대소문자와 공백을 무시하고 장소와 글 내용을 검색한다', () => {
    expect(filterPosts(posts, '추천', '  제주  ').map((post) => post.title)).toEqual(['바다 산책'])
    expect(filterPosts(posts, '추천', '골목').map((post) => post.title)).toEqual(['도시의 밤'])
  })

  test('카테고리와 검색 조건을 함께 적용한다', () => {
    expect(filterPosts(posts, '바다', '부산')).toEqual([])
  })
})
