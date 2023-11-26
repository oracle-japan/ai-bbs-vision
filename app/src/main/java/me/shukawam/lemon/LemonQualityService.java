package me.shukawam.lemon;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.oracle.bmc.aivision.AIServiceVisionClient;
import com.oracle.bmc.aivision.model.AnalyzeImageDetails;
import com.oracle.bmc.aivision.model.AnalyzeImageResult;
import com.oracle.bmc.aivision.model.ImageClassificationFeature;
import com.oracle.bmc.aivision.model.ImageFeature;
import com.oracle.bmc.aivision.model.InlineImageDetails;
import com.oracle.bmc.aivision.requests.AnalyzeImageRequest;

import io.micronaut.context.annotation.Value;
import io.micronaut.http.multipart.StreamingFileUpload;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

@Singleton
public class LemonQualityService {
    private static final Logger logger = LoggerFactory.getLogger(LemonQualityService.class);
    private final AIServiceVisionClient client;

    private final String compartmentOcid;
    private final String modelOcid;

    @Inject
    public LemonQualityService(AIServiceVisionClient client, @Value("${oci.compartment-ocid}") String compartmentOcid,
            @Value("${oci.services.vision.model-ocid}") String modelOcid) {
        this.client = client;
        logger.debug("Initialized config properties. compartmentOcid: %s, modelOcid: %s", compartmentOcid, modelOcid);
        this.compartmentOcid = compartmentOcid;
        this.modelOcid = modelOcid;
    }

    public AnalyzeImageResult analyzeImage(StreamingFileUpload file) {
        List<ImageFeature> features = Arrays.asList(ImageClassificationFeature.builder().modelId(modelOcid).build());
        try {
            var response = client.analyzeImage(
                    AnalyzeImageRequest.builder().analyzeImageDetails(
                            AnalyzeImageDetails.builder().compartmentId(compartmentOcid).image(
                                    InlineImageDetails.builder().data(file.asInputStream().readAllBytes()).build())
                                    .features(features)
                                    .build())
                            .build());
            if (response == null) {
                logger.info("Analyze Image Response is null.");
                throw new RuntimeException();
            }
            return response.getAnalyzeImageResult();
        } catch (IOException e) {
            logger.error("Input file is invalid.", e);
            throw new RuntimeException("Input file is invali.");
        }
    }
}
