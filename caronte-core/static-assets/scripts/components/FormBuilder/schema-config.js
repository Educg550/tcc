// Must mirror FieldTypeEnum in forms/app/entities/Field.py
export const typeRegistry = {
  Text:     { label: 'Text',     hasOptions: false },
  LongText: { label: 'LongText', hasOptions: false },
  Number:   { label: 'Number',   hasOptions: false },
  Radio:    { label: 'Radio',    hasOptions: true  },
  CheckBox: { label: 'CheckBox', hasOptions: true  },
  Date:     { label: 'Date',     hasOptions: false },
  File:     { label: 'File',     hasOptions: false },
}

export function deriveConfig(schema) {
  const requiredFields = schema.required || []
  const sectionItems = schema.properties?.sections?.items || {}
  const sectionRequired = sectionItems.required || []
  const fieldItems = sectionItems.properties?.fields?.items || {}
  const fieldPropsMap = fieldItems.properties || {}
  const fieldRequiredList = fieldItems.required || []

  const fieldProperties = []
  for (const [name, prop] of Object.entries(fieldPropsMap)) {
    let inputType
    if (prop.$ref === '#/$defs/i18n') {
      inputType = 'i18n'
    } else if (prop.type === 'string') {
      inputType = 'text'
    } else if (prop.type === 'boolean') {
      inputType = 'checkbox'
    } else if (prop.type === 'integer') {
      inputType = 'number'
    } else {
      continue
    }
    fieldProperties.push({
      name,
      inputType,
      isI18n: inputType === 'i18n',
      isRequired: fieldRequiredList.includes(name),
    })
  }

  const i18nRef = '#/$defs/i18n'
  // builder.js createInitialState and checkValidity depend on this list:
  // createInitialState seeds state[name] for each entry; checkValidity gates on state.title.pt.
  const topLevelI18nFields = Object.entries(schema.properties || {})
    .filter(([, prop]) => prop.$ref === i18nRef)
    .map(([name]) => ({ name, required: requiredFields.includes(name) }))

  return {
    requiredFields,
    sectionRequired,
    fieldProperties,
    fieldTypes: { ...typeRegistry },
    topLevelI18nFields,
  }
}
