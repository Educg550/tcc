export type MappingType = "candidate" | "recommender";

class MappingService {
	private mappingSegment(formType: MappingType) {
		return formType === "candidate" ? "candidates" : "recommenders";
	}

	async createMapping(
		edictId: string | number,
		formId: string | number,
		version: number,
		formType: MappingType,
		mapping: object,
	) {
		const response = await fetch(
			`/prejanus/${edictId}/${this.mappingSegment(formType)}/mappings/versions/${version}`,
			{
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(mapping),
			},
		);

		if (!response.ok) {
			throw await response.json();
		}

		return response.json();
	}

	async updateMapping(
		edictId: string | number,
		formType: MappingType,
		version: number,
		mappingId: string | number,
		mapping: object,
	) {
		const response = await fetch(
			`/prejanus/${edictId}/${this.mappingSegment(formType)}/mappings/versions/${version}/${mappingId}`,
			{
				method: "PUT",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(mapping),
			},
		);

		if (!response.ok) {
			throw await response.json();
		}

		return response.json();
	}

	async deleteMapping(
		edictId: string | number,
		formType: MappingType,
		version: number,
		mappingId: string | number,
	) {
		const response = await fetch(
			`/prejanus/${edictId}/${this.mappingSegment(formType)}/mappings/versions/${version}/${mappingId}`,
			{
				method: "DELETE",
			},
		);

		if (!response.ok) {
			throw await response.json();
		}
	}

	getMappingsUrl(edictId: string | number, formType: MappingType) {
		return `/${edictId}/${this.mappingSegment(formType)}/mappings`;
	}

	getUnmappedVersionsUrl(edictId: string | number) {
		return `/${edictId}/candidates/forms/versions/unmapped`;
	}

	getFormStructureUrl(formId: string | number, version?: number | string) {
		return version
			? `/api/forms/${formId}?version=${version}`
			: `/api/forms/${formId}`;
	}

	getCloseEdictUrl(edictId: string | number) {
		return `/edicts/${edictId}/close`;
	}

	getSlotsUrl(edictId: string | number) {
		return `/edicts/${edictId}/slots`;
	}
}

export const mappingService = new MappingService();
