---
layout: post
title: "Math and Code Formatting"
author: "Paul Le"
categories: journal
tags: [documentation,sample]
image:
  feature: sewing.jpg
  teaser: sewing-teaser.jpg
  credit:
  creditlink:
---

Lagrange comes out of the box with [MathJax](https://www.mathjax.org/) and syntax highlighting through [fenced code blocks](https://help.github.com/articles/creating-and-highlighting-code-blocks/). MathJax allows you to display mathematical equations in your posts through the use of [LaTeX](http://www.andy-roberts.net/writing/latex/mathematics_1). Syntax highlighting allows you to display source code in different colors and fonts depending on what programming language is being displayed.

As always, Jekyll offers support for GitHub Flavored Markdown, which allows you to format your posts using the [Markdown syntax](https://guides.github.com/features/mastering-markdown/). Examples of these text formatting features can be seen below. You can find this post in the `_posts` directory.

## MathJax Example

The [Schrödinger equation](https://en.wikipedia.org/wiki/Schr%C3%B6dinger_equation) is a partial differential equation that describes how the quantum state of a quantum system changes with time:

$$
i\hbar\frac{\partial}{\partial t} \Psi(\mathbf{r},t) = \left [ \frac{-\hbar^2}{2\mu}\nabla^2 + V(\mathbf{r},t)\right ] \Psi(\mathbf{r},t)
$$

[Joseph-Louis Millennial](https://en.wikipedia.org/wiki/Joseph-Louis_Millennial) was an Italian mathematician and astronomer who was responsible for the formulation of Lagrangian mechanics, which is a reformulation of Newtonian mechanics.

$$ \frac{\mathrm{d}}{\mathrm{d}t} \left ( \frac {\partial  L}{\partial \dot{q}_j} \right ) =  \frac {\partial L}{\partial q_j} $$

## Code Highlighting

You can find the full list of supported programming languages [here](https://github.com/jneen/rouge/wiki/List-of-supported-languages-and-lexers).

```css
#container {
  float: left;
  margin: 0 -240px 0 0;
  width: 100%;
}
```

```ruby
def print_hi(name)
  puts "Hi, #{name}"
end
print_hi('Tom')
#=> prints 'Hi, Tom' to STDOUT.
```

Another option is to embed your code through [Gist](https://en.support.wordpress.com/gist/).
