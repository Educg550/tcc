import { MappingTypeNode } from "../app/[processId]/models/mapping";

export function parseFormData(properties: MappingTypeNode, path = ""): any {
	let result: any = {};

	Object.entries(properties).forEach(([key, value]) => {
		const fullKey = path ? `${path}.${key}` : key;

		if (typeof value === "object") {
			Object.assign(result, parseFormData(value, fullKey));
		} else {
			result[fullKey] = {
				section: null,
				field: null,
			};
		}
	});

	return result;
}

// Extrai todas as chaves de nós intermediários (não-folhas) para controle de expansão
export function parseNodeKeys(node: MappingTypeNode, path = ""): string[] {
	const keys: string[] = [];

	Object.entries(node).forEach(([key, value]) => {
		const fullKey = path ? `${path}.${key}` : key;

		if (typeof value === "object") {
			keys.push(fullKey);
			keys.push(...parseNodeKeys(value as MappingTypeNode, fullKey));
		}
	});

	return keys;
}

/*
 * Converte um objeto com chaves em notação de caminho
 * para uma estrutura hierárquica aninhada.
 *
 * Exemplo:
 *
 * Entrada:
 * {
 *   "address.city": "Araraquara"
 * }
 *
 * Saída:
 * {
 *   address: {
 *     city: "Araraquara"
 *   }
 * }
 *
 * Cada chave é dividida pelo caractere "." e utilizada para construir
 * os níveis intermediários do objeto resultante.
 *
 * @param flat Objeto cujas chaves representam caminhos hierárquicos.
 * @returns Objeto aninhado equivalente à estrutura representada pelas chaves.
 */
export function flatToTree(
	flat: Record<string, { section: number | null; field: number | null }>,
) {
	const result: Record<string, any> = {};

	Object.entries(flat).forEach(([key, value]) => {
		const parts = key.split(".");
		let current = result;

		parts.forEach((part, index) => {
			if (index === parts.length - 1) {
				current[part] = value;
			} else {
				current[part] ??= {};
				current = current[part];
			}
		});
	});

	return result;
}

/*
 * Esta função é a inversa de flatToTree, ou seja, transforma
 *
 * {
 *   key1: {
 *     key2: "foo"
 *   }
 * }
 *
 * em
 *
 * {
 *   "key1.key2": "foo"
 * }
 *
 * @param obj Objeto hierárquico a ser achatado.
 * @returns Objeto plano cujas chaves representam caminhos hierárquicos
 * separados por ".".
 */
export function treeToFlat(
	obj: Record<string, any>,
	path = "",
): Record<string, { section: number | null; field: number | null }> {
	const result: Record<string, any> = {};

	Object.entries(obj).forEach(([key, value]) => {
		const fullKey = path ? `${path}.${key}` : key;

		const isLeaf =
			value &&
			typeof value === "object" &&
			"section" in value &&
			"field" in value;

		if (isLeaf) {
			result[fullKey] = value;
		} else if (value && typeof value === "object") {
			Object.assign(result, treeToFlat(value, fullKey));
		}
	});

	return result;
}
