/*
 * Copyright (c) 2023 Airbyte, Inc., all rights reserved.
 */
package io.airbyte.cdk.test.fixtures.legacy

import io.airbyte.protocol.models.ConfiguredAirbyteCatalog

class DefaultProtocolSerializer : ProtocolSerializer {
    override fun serialize(configuredAirbyteCatalog: ConfiguredAirbyteCatalog): String {
        return Jsons.serialize(configuredAirbyteCatalog)
    }
}
