import path from 'path'
import MiniCssExtractPlugin from 'mini-css-extract-plugin'
import CssMinimizerPlugin from 'css-minimizer-webpack-plugin'
import IgnoreEmitPlugin from 'ignore-emit-webpack-plugin'
import CopyPlugin from "copy-webpack-plugin"
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export default [
    {
        mode: 'production',
        name: "styles",
        entry: {
            main: [
                './styles/variables.css',
                './styles/reset.css',
                './styles/main.css',
                './styles/text.css',
            ],
            form: [
                './styles/form.css',
                './styles/form-builder.css'
            ],
            mobile: [
                './styles/mobile.css'
            ]
        },
        output: {
            path: path.resolve(__dirname, 'dist'),
            filename: '[name].bundle.min.js'
        },
        module: {
            rules: [
                {
                    test: /\.css$/i,
                    use: [MiniCssExtractPlugin.loader, 'css-loader'],
                },
            ],
        },
        optimization: {
            minimize: true,
            minimizer: [new CssMinimizerPlugin()]
        },
        plugins: [
            new MiniCssExtractPlugin({ filename: '[name].bundle.min.css' }),
            new IgnoreEmitPlugin(/.*\.bundle\.min\.js$/)
        ],
    }, {
        mode: 'production',
        name: "scripts",
        entry: [
            "./scripts/app.js"
        ],
        output: {
            path: path.resolve(__dirname, 'dist'),
            filename: 'bundle.min.js'
        },
        module: {
            rules: [
                {
                    test: /\.css$/i,
                    use: [
                        {
                            loader: "style-loader",
                            options: { 
                                injectType: "lazyStyleTag",
                                insert: path.resolve(__dirname, "insert-function.js")
                            }
                        },
                        {
                            loader: 'css-loader',
                            options: {
                                modules: {
                                    localIdentName: '[local]'
                                }
                            }
                        }
                    ],
                },
            ],
        }
    }, {
        name: "copy-images",
        mode: "production",
        entry: {},
        output: {
            path: path.resolve(__dirname, "dist"),
            filename: "bundle.js",
        },
        plugins: [
            new CopyPlugin({
            patterns: [
                    {
                        from: path.resolve(__dirname, "favicon.ico"),
                        to: "favicon.ico",
                    },
                    {
                        from: path.resolve(__dirname, "site.webmanifest"),
                        to: "site.webmanifest",
                    },
                    {
                        from: path.resolve(__dirname, "images"),
                        to: "images",
                    },
                ],
            }),
        ],
    }, {
        name: "copy-schemas",
        mode: "production",
        entry: {},
        output: {
            path: path.resolve(__dirname, "dist"),
            filename: "bundle.js",
        },
        plugins: [
            new CopyPlugin({
            patterns: [
                    {
                        from: path.resolve(__dirname, "schema"),
                        to: "schema",
                        noErrorOnMissing: true,
                    },
                ],
            }),
        ],
    }
]