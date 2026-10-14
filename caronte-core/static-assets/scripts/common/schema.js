import { autocompletion } from "@codemirror/autocomplete"
import { linter } from "@codemirror/lint"
import Ajv from "ajv"

export async function loadSchema(url) {
    try {
        const ajv = new Ajv({ allErrors: true })

        const response = await fetch(url)
        if (!response.ok) throw new Error(`Erro ao carregar schema: ${response.status}`)
        const schema = await response.json()
        return { schema, validate: ajv.compile(schema) }
    } catch (err) {
        console.error(err)
        return null
    }
}

export const jsonSchemaLinter = (validate) => {
    return linter((view) => {
        const text = view.state.doc.toString()
        let errors = []
        try {
            const data = JSON.parse(text)
            const valid = validate(data)
            if (!valid) {
                errors = validate.errors.map(err => ({
                    from: 0,
                    to: view.state.doc.length,
                    severity: "error",
                    message: `${err.instancePath} ${err.message}`
                }))
            }
        } catch (e) {
            errors = [{
                from: 0,
                to: view.state.doc.length,
                severity: "error",
                message: e.message
            }]
        }
        return errors
    })
}