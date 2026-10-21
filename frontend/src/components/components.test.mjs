import { describe, expect, test } from '@jest/globals'
import { readFileSync, readdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { compileScript, compileTemplate, parse } from '@vue/compiler-sfc'

const componentsRoot = dirname(fileURLToPath(import.meta.url))
const componentFiles = readdirSync(componentsRoot).filter((filename) => filename.endsWith('.vue') && filename !== 'PostList.vue')

describe('course component Vue templates', () => {
  test.each(componentFiles)('%s parses and compiles', (filename) => {
    const source = readFileSync(resolve(componentsRoot, filename), 'utf8')
    const { descriptor, errors } = parse(source, { filename })
    expect(errors).toEqual([])

    const script = compileScript(descriptor, { id: filename })
    const template = compileTemplate({
      source: descriptor.template.content,
      filename,
      id: filename,
      compilerOptions: { bindingMetadata: script.bindings },
    })

    expect(template.errors).toEqual([])
  })
})
