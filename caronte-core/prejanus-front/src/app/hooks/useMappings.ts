import useSWR from "swr";
import { mutate } from "swr";

import { TMapping } from "@/app/[processId]/models/mapping";
import { mappingService, MappingType } from "@/services/mappingService";

export function useMappings(processId: string | number, formType: MappingType) {
	const {
		data,
		error,
		isLoading,
		mutate: mutateMappings,
	} = useSWR<TMapping[]>(mappingService.getMappingsUrl(processId, formType));

	const createMapping = async (
		formId: string | number,
		version: number,
		mapping: object,
	) => {
		const result = await mappingService.createMapping(
			processId,
			formId,
			version,
			formType,
			mapping,
		);

		await mutateMappings();
		await mutate(`/${processId}/${formType}s/forms/versions/unmapped`);

		return result;
	};

	const updateMapping = async (
		version: number,
		mappingId: string | number,
		mapping: object,
	) => {
		const result = await mappingService.updateMapping(
			processId,
			formType,
			version,
			mappingId,
			mapping,
		);

		await mutateMappings();
		await mutate(`/${processId}/${formType}s/forms/versions/unmapped`);

		return result;
	};

	const deleteMapping = async (
		version: number,
		mappingId: string | number,
	) => {
		await mappingService.deleteMapping(
			processId,
			formType,
			version,
			mappingId,
		);

		await mutateMappings();
		await mutate(`/${processId}/${formType}s/forms/versions/unmapped`);
	};

	return {
		mappings: data ?? [],
		error,
		isLoading,
		refresh: mutateMappings,
		createMapping,
		updateMapping,
		deleteMapping,
	};
}
